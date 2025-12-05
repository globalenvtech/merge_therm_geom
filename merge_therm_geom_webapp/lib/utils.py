import io
import geomie3d
import numpy as np
from stl import mesh
from plyfile import PlyData, PlyElement

from pyscript import document
from js import Uint8Array, File, URL

def convertxyz2zxy(xyzs: np.ndarray):
    """
    convert xyzs from xyz cs to zxy coordinate

    Parameters
    ----------
    xyzs : np.ndarray
        np.ndarray[shape(npoints, 3)] 

    Returns
    -------
    np.ndarray
        np.ndarray[shape(npoints, 3)]
    """
    orig_cs = geomie3d.utility.CoordinateSystem([0,0,0], [1,0,0], [0,1,0])
    dest_cs = geomie3d.utility.CoordinateSystem([0,0,0], [0,0,1], [1,0,0])
    trsf_mat = geomie3d.calculate.cs2cs_matrice(orig_cs, dest_cs)
    trsf_xyzs = geomie3d.calculate.trsf_xyzs(xyzs, trsf_mat)
    return trsf_xyzs

def read_stl_web(stl_bytes: bytes) -> dict:
    """
    read stl file for webapp

    Parameters
    ----------
    stl_bytes: bytes
        JS bytes from the file specified  

    Returns
    -------
    dict
        A dictionary containing:
            - "xyzs": np.ndarray[(n_triangles, 3, 3)].
    """
    stl_bytes = stl_bytes.to_py()
    stl_bstream = io.BytesIO(stl_bytes)
    stl_mesh = mesh.Mesh.from_file('', fh=stl_bstream)
    mesh_data = stl_mesh.vectors
    return {'xyzs': mesh_data}

def read_ply_web(ply_bytes: bytes) -> dict:
    """
    read ply file for webapp

    Parameters
    ----------
    ply_bytes: bytes
        JS bytes from the file specified  

    Returns
    -------
    np.ndarray
        np.ndarray[(n_points, n_attributes)]
    """
    ply_bytes = ply_bytes.to_py()
    bstream = io.BytesIO(ply_bytes)
    plydata = PlyData.read(bstream)
    data = plydata['vertex'].data
    data = list(map(list, data))
    data = np.array(data)
    return data

def write_ply_web(vertex_data: list[tuple], dtype_val: list[tuple]) -> io.BytesIO:
    ply_vertex_data = np.array(vertex_data, dtype=dtype_val)
    element = PlyElement.describe(ply_vertex_data, 'vertex')
    ply = PlyData([element], text=True)

    # Write to BytesIO
    buffer = io.BytesIO()
    ply.write(buffer)
    return buffer
        
def create_hidden_link(bstream: io.BytesIO, file_name: str, file_type: str):
    buffer = bstream.getbuffer()
    nbuffer = len(buffer)
    js_array = Uint8Array.new(nbuffer)
    js_array.assign(buffer)

    file = File.new([js_array], file_name, {type: f"application/{file_type}"})
    url = URL.createObjectURL(file)

    hidden_link = document.createElement("a")
    hidden_link.setAttribute("download", f"{file_name}.{file_type}")
    hidden_link.setAttribute("href", url)
    hidden_link.click()

def rgb_falsecolors(vals, minval, mxval):
    rgbs = geomie3d.utility.calc_falsecolour(vals, minval, mxval)
    rgbs_flat = np.array(rgbs).flatten().tolist()
    return rgbs_flat