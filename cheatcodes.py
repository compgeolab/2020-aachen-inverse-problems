"""
Code for cheating in the inversion programming.

Includes functions for:

* forward modelling with prisms
* generating a synthetic model
* plotting the models and solutions

"""
import numpy as np
import matplotlib.pyplot as plt


def plot_prisms(
    depths,
    basin_boundaries,
    ax=None,
    color="#00000000",
    edgecolor="black",
    linewidth=1,
    label=None,
    figsize=(9, 3),
):
    """
    Plot the prism model using matplotlib.
    """
    # Create lines with the outline of the prisms
    boundaries = np.linspace(*basin_boundaries, depths.size + 1)
    x = [boundaries[0]]
    y = [0]
    for i in range(depths.size):
        x.extend([boundaries[i], boundaries[i + 1]])
        y.extend([depths[i], depths[i]])
    x.append(boundaries[-1])
    y.append(0)
    x = np.array(x) / 1000
    y = np.array(y) / 1000
    # Plot the outline with optional filling
    if ax is None:
        fig = plt.figure(figsize=figsize)
        ax = plt.subplot(111)
        ax.set_xlabel("x [km]")
        ax.set_ylabel("depth [km]")
    ax.fill_between(
        x, y, color=color, edgecolor=edgecolor, linewidth=linewidth, label=label
    )
    ax.set_ylim(max(y) * 1.05, 0)
    return ax


def gaussian(x, shift, std, amplitude):
    """
    A simple Gaussian function we'll use to make a model
    """
    return amplitude * np.exp(-(((x - shift) / std) ** 2))


def synthetic_model():
    """
    Generate a synthetic model using Gaussian functions
    """
    size = 100
    basin_boundaries = (0, 100e3)
    boundaries = np.linspace(*basin_boundaries, size + 1)
    x = boundaries[:-1] + 0.5 * (boundaries[1] - boundaries[0])
    depths = gaussian(x, shift=45e3, std=20e3, amplitude=5e3) + gaussian(
        x, shift=80e3, std=10e3, amplitude=1e3
    )
    # Make sure the boundaries are at zero to avoid steps
    depths -= depths.min()
    return depths, basin_boundaries


def make_prisms(depths, basin_boundaries):
    """
    Generate a list of 3D prisms from the depths and boundaries.
    """
    boundaries = np.linspace(*basin_boundaries, depths.size + 1)
    infinity = np.full_like(depths, 500e3)
    prisms = np.transpose(
        [
            boundaries[:-1],  # east
            boundaries[1:],  # west
            -infinity,  # south
            infinity,  # north
            -depths,  # bottom
            np.zeros_like(depths),  # top
        ]
    )
    return prisms


def forward_model(depths, basin_boundaries, density, x):
    """
    Calculate the predicted gravity for a given basin at x locations
    """
    # Computation points
    easting = x
    northing = np.zeros_like(x)
    upward = np.zeros_like(x) + 1
    prisms = make_prisms(depths, basin_boundaries)
    result = np.zeros_like(x)
    for m in range(prisms.shape[0]):
        # Iterate over the prism boundaries to compute the result of the
        # integration (see Nagy et al., 2000)
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    shift_east = prisms[m, 1 - i]
                    shift_north = prisms[m, 3 - j]
                    shift_upward = prisms[m, 5 - k]
                    result += (-1) ** (i + j + k) * kernel(
                        shift_east - easting,
                        shift_north - northing,
                        shift_upward - upward,
                    )
    si2mgal = 1e5
    # The gravitational constant in SI units
    GRAVITATIONAL_CONST = 0.00000000006673
    result *= GRAVITATIONAL_CONST * density * si2mgal
    return result


def kernel(easting, northing, upward):
    """
    The kernel function for calculating the vertical component of gravity
    """
    radius = np.sqrt(easting ** 2 + northing ** 2 + upward ** 2)
    result = (
        easting * np.log(northing + radius)
        + northing * np.log(easting + radius)
        + upward * np.arctan2(easting * northing, -upward * radius)
    )
    return result
