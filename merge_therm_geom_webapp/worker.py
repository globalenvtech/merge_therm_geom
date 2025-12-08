import geomie3d
import numpy as np

from raytrace_mrt_lib import separate_rays
from pyscript_3dapp_lib.utils import convertxyz2zxy, read_stl_web, read_ply_web
from pyscript import sync

def process_plydata(plydata: np.ndarray) -> dict:
    """
    separate the plydata into xyzs and temperatures

    Parameters
    ----------
    plydata: np.ndarray
        np.ndarray[shape(n_pts, n_attributes)] 

    Returns
    -------
    dict
        A dictionary containing:
            - "xyzs": np.ndarray[(n_pts, 3)].
            - "temps": np.ndarray[(n_pts)].
    """
    temps = plydata[:, 3]
    temp_dicts = []
    for temp in temps:
        temp_dicts.append({'temperature': temp})

    vertices = plydata[:, 0:3]
    return {'xyzs': vertices, 'temps': temp_dicts}

def mesh2pts(mesh_xyzs: np.ndarray):
    """
    sort mesh data into points

    Parameters
    ----------
    mesh_xyzs : np.ndarray
        np.ndarray[shape(ntri, 3, 3)] 

    Returns
    -------
    np.ndarray
        np.ndarray[shape(ntri * 3, 3)]
    """
    ntri = len(mesh_xyzs)
    mesh_points = np.reshape(mesh_xyzs, (ntri*3, 3))
    return mesh_points

def proj_therm2stl(ply_bytes: bytes, stl_bytes: bytes, sensor_pos: list) -> dict:
    """
    project thermal point cloud onto stl file

    Parameters
    ----------
    ply_bytes: bytes
        np.ndarray[shape(ntri, 3, 3)] 

    Returns
    -------
    flatten_mesh_xyzs : np.ndarray
        np.ndarray[shape(ntri * 3 * 3)]
    """
    #------------------------------------------------------------------
    # region: read stl file 
    sync.change_dialog_text('Reading STL file ...')
    stldata = read_stl_web(stl_bytes)
    stl_xyzs = stldata['xyzs']
    tri_ls = []
    for tri in stl_xyzs:
        tri_verts = geomie3d.create.vertex_list(tri)
        tri_face = geomie3d.create.polygon_face_frm_verts(tri_verts)
        tri_ls.append(tri_face)
    # endregion: read stl file
    #------------------------------------------------------------------
    # region: read ply file
    sync.change_dialog_text('Reading PLY file ...')
    plydata = read_ply_web(ply_bytes)
    plydata = process_plydata(plydata)
    ply_xyzs = plydata['xyzs']
    temps = plydata['temps']
    sync.change_dialog_text('Moving PLY pts to sensor position ...')
    gverts = geomie3d.create.vertex_list(ply_xyzs, attributes_list=temps)
    vcomp = geomie3d.create.composite(gverts)
    mv_vcomp = geomie3d.modify.move_topo(vcomp, sensor_pos)
    mv_gverts = geomie3d.get.topo_explorer(mv_vcomp, geomie3d.topobj.TopoType.VERTEX)
    # endregion: read ply file
    #------------------------------------------------------------------
    # region: convert the ply data to rays
    sync.change_dialog_text('Converting PLY pts to rays ...')
    
    rays = []
    for vcnt,v in enumerate(gverts):
        temp = v.attributes['temperature']
        ray = geomie3d.create.ray(sensor_pos, v.point.xyz, attributes = {'temperature':temp, 'id': vcnt})
        rays.append(ray)
    
    aloop = 1000000#30
    ntri = len(stl_xyzs)
    ndir = len(mv_gverts)
    ttl = ndir*ntri
    nparallel = int(ttl/aloop)
    
    if nparallel != 0:
        rays_ls = separate_rays(rays, nparallel)
    # endregion: convert the ply data to rays
    #------------------------------------------------------------------
    # region: project the thermal scan onto stl triangle faces
    sync.change_dialog_text('Projecting PLY ray onto STL triangles ...')
    ttl_k = int(ttl/1000)
    proj_rays = []
    rcnt = 0
    for rays1 in rays_ls:
        rcnt += len(rays1)
        percentage = int((rcnt*ntri)/ttl * 100)
        hrs, mrs, hfs, mfs = geomie3d.calculate.rays_faces_intersection(rays1, tri_ls)
        nhr = len(hrs)
        nmr = len(mrs)
        msg = f"Projecting {ndir} PLY ray onto {ntri} STL triangles ... \n{percentage}% of {ttl_k}k calculations completed"
        msg += f"\n{nhr} rays intersection, {nmr} rays did not hit any surfaces"
        sync.change_dialog_text(msg)
        proj_rays.extend(hrs)
    # endregion: project the thermal scan onto stl triangle faces
    #------------------------------------------------------------------
    # region: prepare data
    # stl triangles
    stl_pts_xyzs = mesh2pts(stl_xyzs)
    stl_pts_zxys = convertxyz2zxy(stl_pts_xyzs)
    stl_pts_zxys_flatten = stl_pts_zxys.flatten().tolist()

    bbox = geomie3d.calculate.bbox_frm_xyzs(stl_pts_xyzs)
    bbox_arr = bbox.bbox_arr
    cam_pos = [bbox_arr[3]+5, bbox_arr[4]+5, bbox_arr[5]+5]
    bbox_midpt = geomie3d.calculate.bboxes_centre([bbox])[0].tolist()
    cam_place = [cam_pos, bbox_midpt]
    cam_place_zxy = convertxyz2zxy(cam_place)
    # ply pts
    proj_xyzs = []
    ply_verts = []
    temps = []
    for proj_ray in proj_rays:
        intx = proj_ray.attributes['rays_faces_intersection']['intersection'][0]
        temp = float(proj_ray.attributes['temperature'])
        temps.append(temp)
        ply_verts.append((intx[0], intx[1], intx[2], temp))
        proj_xyzs.append(intx)
    
    proj_xyzs = convertxyz2zxy(proj_xyzs)
    proj_xyzs_flatten = np.array(proj_xyzs).flatten().tolist()
    return {'stl': stl_pts_zxys_flatten, 'proj_ply_viz': proj_xyzs_flatten, 
            'proj_ply_write': ply_verts, 'temps': temps, 'cam': cam_place_zxy}
    # endregion: prepare data
    #------------------------------------------------------------------

sync.proj_therm2stl = proj_therm2stl