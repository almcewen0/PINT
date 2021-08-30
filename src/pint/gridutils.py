"""Tools for building chi-squared grids."""
import copy
import multiprocessing
import os
from multiprocessing import Process, Queue
from pathos.multiprocessing import ProcessingPool as Pool

import astropy.constants as const
import astropy.units as u
import numpy as np

import pint.utils

__all__ = ["grid_chisq", "grid_chisq_mp", "plot_grid_chisq"]


def _grid_docol(ftr, par1_name, par1, par2_name, par2_grid):
    """Worker process that computes one row of the chisq grid"""
    chisq = np.zeros(len(par2_grid))
    for jj, par2 in enumerate(par2_grid):
        # Make a full copy of the fitter to work with
        myftr = copy.deepcopy(ftr)
        # Freeze the two params we are going to grid over and set their values
        # All other unfrozen parameters will be fitted for at each grid point
        getattr(myftr.model, par1_name).frozen = True
        getattr(myftr.model, par2_name).frozen = True
        getattr(myftr.model, par1_name).quantity = par1
        getattr(myftr.model, par2_name).quantity = par2
        chisq[jj] = myftr.fit_toas()
    return chisq


def _grid_doonefit(ftr, parnames, parvalues):
    """Worker process that computes one fit for the chisq grid"""
    # Make a full copy of the fitter to work with
    myftr = copy.deepcopy(ftr)
    for parname, parvalue in zip(parnames, parvalues):
        # Freeze the  params we are going to grid over and set their values
        # All other unfrozen parameters will be fitted for at each grid point
        getattr(myftr.model, parname).frozen = True
        getattr(myftr.model, parname).quantity = parvalue
    return myftr.fit_toas()


def grid_chisq_mp(ftr, parnames, parvalues, ncpu=None):
    """Compute chisq over a grid of two parameters, multiprocessing version

    Use pathos's multiprocessing package to do a parallel computation of
    chisq over 2-D grid of parameters.  Need this instead of stock python because
    of unpicklable objects.

    Parameters
    ----------
    ftr
        The base fitter to use.
    parnames : list
        Names of the parameters to grid over
    parvalues : list
        List of parameter values to grid over (each should be array of Quantity)
    ncpu : int, optional
        Number of processes to use in parallel. Default is number of CPUs available

    Returns
    -------
    array : 2-D array of chisq values with par1 varying in columns and par2 varying in rows
    """

    if ncpu is None:
        # Use al available CPUs
        ncpu = multiprocessing.cpu_count()

    pool = Pool(ncpu)
    out = np.meshgrid(*parvalues)
    chi2 = np.zeros(out[0].shape)
    it = np.nditer(out[0], flags=["multi_index"])

    # First create all the processes and put them in a pool
    results = pool.map(
        _grid_doonefit,
        (ftr,) * len(out[0].flatten()),
        (parnames,) * len(out[0].flatten()),
        list(zip(*[x.flatten() for x in out])),
    )
    for j, x in enumerate(it):
        chi2[it.multi_index] = results[j]

    return chi2


def grid_chisq(ftr, parnames, parvalues, printprogress=True):
    """Compute chisq over a grid of two parameters, serial version

    Single-threaded computation of chisq over 2-D grid of parameters.

    Parameters
    ----------
    ftr
        The base fitter to use.
    parnames : list
        Names of the parameters to grid over
    parvalues : list
        List of parameter values to grid over (each should be array of Quantity)
    printprogress : bool, optional
        Print indications of progress

    Returns
    -------
    array : 2-D array of chisq values 

    """

    # Save the current model so we can tweak it for gridding, then restore it at the end
    savemod = ftr.model
    gridmod = copy.deepcopy(ftr.model)
    ftr.model = gridmod

    # Freeze the  params we are going to grid over
    for parname in parnames:
        getattr(ftr.model, parname).frozen = True

    # All other unfrozen parameters will be fitted for at each grid point
    out = np.meshgrid(*parvalues)
    chi2 = np.zeros(out[0].shape)
    it = np.nditer(out[0], flags=["multi_index"])
    for x in it:
        for parnum, parname in enumerate(parnames):
            getattr(ftr.model, parname).quantity = out[parnum][it.multi_index]
        chi2[it.multi_index] = ftr.fit_toas()
        if printprogress:
            print(".", end="")

    if printprogress:
        print("")

    # Restore saved model
    ftr.model = savemod
    return chi2


def grid_chisq_derived(
    ftr,
    par1_name,
    par1_func,
    axis1_grid,
    par2_name,
    par2_func,
    axis2_grid,
    printprogress=True,
):
    """Compute chisq over a grid of two parameters, serial version

    Single-threaded computation of chisq over 2-D grid of parameters.

    Parameters
    ----------
    ftr
        The base fitter to use.
    par1_name : str
        Name of the first parameter to grid over
    par1_func : function
        Function to compute `par1` based on (`axis1`,`axis2`)
    axis1_grid : array, Quantity
        Array of values for column of the input matrix
    par2_name : str
        Name of the second parameter to grid over
    par2_func : function
        Function to compute `par2` based on (`axis1`,`axis2`)
    axis2_grid : array, Quantity
        Array of values for column of the input matrix
    printprogress : bool, optional
        Print indications of progress

    Returns
    -------
    array : 2-D array of chisq values with `par1` varying in columns and `par2` varying in rows
    par1 : parameter1 derived from `axis1`, `axis2` according to `par1_func`
    par2 : parameter2 derived from `axis1`, `axis2` according to `par2_func`
    """

    # Save the current model so we can tweak it for gridding, then restore it at the end
    savemod = ftr.model
    gridmod = copy.deepcopy(ftr.model)
    ftr.model = gridmod

    # Freeze the two params we are going to grid over
    getattr(ftr.model, par1_name).frozen = True
    getattr(ftr.model, par2_name).frozen = True

    # All other unfrozen parameters will be fitted for at each grid point

    chi2 = np.zeros((len(axis2_grid), len(axis1_grid)))
    par1 = (
        np.zeros((len(axis2_grid), len(axis1_grid)))
        * getattr(ftr.model, par1_name).units
    )
    par2 = (
        np.zeros((len(axis2_grid), len(axis1_grid)))
        * getattr(ftr.model, par2_name).units
    )

    # Want par1 on X-axis and par2 on y-axis
    for ii, axis1 in enumerate(axis1_grid):
        for jj, axis2 in enumerate(axis2_grid):
            par1[jj, ii] = par1_func(axis1, axis2)
            par2[jj, ii] = par2_func(axis1, axis2)

            getattr(ftr.model, par1_name).quantity = par1[jj, ii]
            getattr(ftr.model, par2_name).quantity = par2[jj, ii]

            # Array index here is rownum, colnum so translates to y, x
            chi2[jj, ii] = ftr.fit_toas()
            if printprogress:
                print(".", end="")
        if printprogress:
            print("")

    # Restore saved model
    ftr.model = savemod
    return chi2, par1, par2


def plot_grid_chisq(
    par1_name, par1_grid, par2_name, par2_grid, chi2, title="Chisq Heatmap"
):
    """Plot results of chi2 grid

    Parameters
    ----------
    ftr
        The base fitter to use.
    par1_name : str
        Name of the first parameter to grid over
    par1_grid : array, Quantity
        Array of par1 values for column of the output matrix
    par2_name : str
        Name of the second parameter to grid over
    par2_grid : array, Quantity
        Array of par2 values for column of the output matrix
    title : str, optional
        Title for plot
    """

    import matplotlib.pyplot as plt

    # Compute chi2 difference from minimum
    delchi2 = chi2 - chi2.min()
    fig, ax = plt.subplots(figsize=(9, 9))
    delta_par1 = (par1_grid[1] - par1_grid[0]).value
    delta_par2 = (par2_grid[1] - par2_grid[0]).value
    ax.imshow(
        delchi2,
        origin="lower",
        extent=(
            par1_grid[0].value - delta_par1 / 2,
            par1_grid[-1].value + delta_par1 / 2,
            par2_grid[0] - delta_par2 / 2,
            par2_grid[-1] + delta_par2 / 2,
        ),
        aspect="auto",
        cmap="Blues_r",
        interpolation="bicubic",
        vmin=0,
        vmax=10,
    )
    levels = np.arange(4) + 1
    ax.contour(
        delchi2,
        levels=levels,
        colors="red",
        extent=(
            par1_grid[0].value - delta_par1 / 2,
            par1_grid[-1].value + delta_par1 / 2,
            par2_grid[0] - delta_par2 / 2,
            par2_grid[-1] + delta_par2 / 2,
        ),
    )
    ax.set_xlabel(par1_name)
    ax.set_ylabel(par2_name)
    ax.grid(True)
    ax.set_title(title)
    return
