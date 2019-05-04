import sys
import os
import math
from scipy.spatial import ConvexHull

from utils import fmt

"""
This script applies alpha-shape or simple convex hull
to find the shape of the high-dimensional data points.
Then it saves the layer in a file.
"""

def collapse(points, dim = 0):
    """
    This function collapse one of the n-dimension of the
    data points. By default it collapses the first dimension.
    But in most cases we collapse the last dimension, i.e.
    z-axis in case of 3D points. The parameter dim denotes
    which dimension it's going to collapse.
    """
    points_ = []
    for p in points:
        p_ = [x for i,x in enumerate(p) if i != dim]
        points_.append(p_)
    return points_

def project(points):
    """
    This function projects data point on a simplex hyperplane.
    """
    dim = len(points[0])
    u = [1.0 / math.sqrt(dim) for _ in range(dim)]
    points_ = []
    for p in points:
        uTp = sum([x * u[i] for i, x in enumerate(p)])
        uTpu = [x * uTp for x in u]
        p_ = [(x - uTpu[i]) + u[i]/math.sqrt(dim) for i, x in enumerate(p)]
        points_.append(p_)
    return points_

def get_convex_hull(points, indices):
    """
    For a given set of points and a list of their indices,
    this function returns the list of indices of those points
    that form the convex hull.
    """
    print("Computing alpha-shape ...")
    vmap = {}
    p = []
    for i,idx in enumerate(indices):
        p.append(points[idx])
        vmap[i] = idx
    
    m = len(p[0])
    hull_indices = set()
    if len(p) <= m + 1:
        hull_indices = set(p)
    else:
        hull = ConvexHull(p)
        for simplex in hull.simplices:
            for vertex in simplex:
                hull_indices.add(indices[vertex])
    print("alpha-shape done.")
    return hull_indices

def peel(points):
    """
    This function calls the get_convex_hull() function in a 
    recursive manner to find each layer of the boundary points
    and returns the boundary indices as list of lists.
    """
    m = len(points[0])
    boundaries = []
    all_indices = range(len(points))
    print("Total points:", len(all_indices))
    l = 0
    while len(all_indices) > m + 1:
        hull_indices = get_convex_hull(points, all_indices)
        # If the points are not in "general position", 
        # there might be no hull.
        if len(hull_indices) > 0:
            print("Layer {:d}:".format(l), end = " ")
            boundaries.append(list(hull_indices))
            print("points added {:d}".format(len(hull_indices)), end = ", ")
            all_indices = [x for x in all_indices if x not in hull_indices]
            print("points left {:d}.".format(len(all_indices)))
        else:
            # No hull found. May be the rest of the points are not in
            # general position, now lump them together as one layer.
            break;
        l += 1
    if len(all_indices) > 0:
        print("Layer {:d}:".format(l), end = " ")
        boundaries.append(all_indices)
        print("points added {:d}.".format(len(all_indices)), "\n")
    return boundaries

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 peel.py [normalized data file] [projection option]")
        sys.exit(1)
    
    mode = "default" if len(sys.argv) < 3 else sys.argv[2].strip()
    
    normfpath = sys.argv[1].strip()
    points = fmt.load(normfpath)

    m = len(points[0])
    print("Peeling data point cloud in {0:s} mode ...".format(mode))
    if mode == "default":
        # the defualt mode will project the points 
        # on a simplex on the first quadrant
        ppoints = project(points)
        cpoints = collapse(ppoints, dim = m - 1)
        boundaries = peel(cpoints)
    elif mode == "no-project":
        boundaries = peel(points)
    fmt.cat(boundaries, dtype = 'int')
   
    path, normfname = os.path.split(normfpath)
    layerfpath = os.path.join(path, normfname.split('.')[0] + "-layers.out")
    print("Saving {0:d} layers into {1:s} ...".format(len(boundaries), layerfpath))
    fmt.save(boundaries, layerfpath, dtype = 'int')