import asyncio
from time import perf_counter

from pyodide.ffi.wrappers import add_event_listener
from pyscript.ffi import create_proxy
from pyscript import window, document, PyWorker

from pyscript_3dapp_lib.utils import create_hidden_link, write_ply_web, rgb_falsecolors, convertxyz2zxy, get_bytes_from_file
from pyscript_3dapp_lib.libthree import get_scene, get_camera, get_renderer, get_orbit_ctrl, get_lights, create_tri_mesh, create_grp, create_cube, viz_pts_color, create_sphere

PROJECTED_PTS = None
PLY_NAME = None
height_3dview_ratio = 0.85
# get the renderer and append it to index.html
renderer = get_renderer()
renderer.setSize(window.innerWidth, window.innerHeight*height_3dview_ratio)
bottom_side = document.getElementById('bottomSide')
bottom_side.appendChild(renderer.domElement)
# get the camera and scene
camera = get_camera()
# get the scene
scene = get_scene()
# get lights and put in the scene
lights = get_lights()
for light in lights:
    scene.add(light)
# disable the download button
dl_btn = document.getElementById("st-download")
dl_btn.disabled = True
# orbit controls
controls = get_orbit_ctrl(camera, renderer)

# create a spinning cube
init_cube, init_edges = create_cube()
init_edges.name = 'init_edges'
scene.add(init_edges)

def set_cam_orig():
    camera.position.set(1, 1, 4)
    camera.lookAt(0,0,0)

set_cam_orig()

def animate(*args):
    controls.update()
    init_edges.rotation.x += 0.01
    init_edges.rotation.y += 0.01
    renderer.render(scene, camera)
    # Call the animation loop recursively
    window.requestAnimationFrame(animate_proxy)

animate_proxy = create_proxy(animate)
window.requestAnimationFrame(animate_proxy)

def change_dialog_text(txt: str):
    text_elem = document.getElementById("dialogText")
    text_elem.innerText = txt

def change_color_bar(mnval: float, mxval: float):
    val_range = mxval - mnval
    interval = val_range/4
    intervals = [mnval, mnval+interval, mnval+(interval*2), mnval+(interval*3), mxval]
    for cnt, i in enumerate(intervals):
        color_label = document.getElementById("fcval" + str(cnt+1))
        color_label.textContent = str(round(i, 1))

async def on_pts_submit(e):
    try:
        t1 = perf_counter()
        submit_btn = document.getElementById("stgeom-submit")
        submit_btn.disabled = True
        set_cam_orig()
        init_edges = scene.getObjectByName( "init_edges", True )
        scene.add(init_edges)
        output_p = document.querySelector("#stgeom-output")
        output_p.textContent = 'Reading ...'
        st_file_input = document.querySelector("#stpts-file-upload")
        geom_file_input = document.querySelector("#geom-file-upload")
        st_file_list = st_file_input.files
        geom_file_list = geom_file_input.files
        nstfiles = len(st_file_list)
        ngfiles = len(geom_file_list)
        
        if nstfiles != 0 and ngfiles != 0:
            # loading dialog to inform users processing in progress
            loading_dialog = document.getElementById("loading")
            loading_dialog.showModal()
            st_item = st_file_list.item(0)
            global PLY_NAME
            st_full_name = st_item.name
            st_name = st_full_name.split('.')[0]
            PLY_NAME = st_name
            geom_item = geom_file_list.item(0)

            st_bytes = await get_bytes_from_file(st_item)
            geom_bytes = await get_bytes_from_file(geom_item)
            # get the sensor pos
            posx_val = float(document.querySelector("#posx").value)
            posy_val = float(document.querySelector("#posy").value)
            posz_val = float(document.querySelector("#posz").value)
            sensor_pos_zxy = convertxyz2zxy([[posx_val, posy_val, posz_val]])[0]
            # Await for the worker
            worker_config = {
                                "packages": ["plyfile>=1.1.3", "geomie3d==0.0.10", "numpy-stl==3.2.0", 
                                             "./lib/pyscript_3dapp_lib-0.0.1.post3-py3-none-any.whl",
                                             "./lib/raytrace_mrt_lib-0.0.1-py3-none-any.whl"]
                            }
            worker = PyWorker("./worker.py", type="pyodide", config = worker_config)
            # Await for the worker
            await worker.ready
            worker.sync.change_dialog_text = change_dialog_text

            world = create_grp()
            sensor_pos = [posx_val, posy_val, posz_val]
            proj_data = await worker.sync.proj_therm2stl(st_bytes, geom_bytes, sensor_pos)
            stl_xyzs = proj_data.stl
            ply_xyzs_viz = proj_data.proj_ply_viz
            ply_write = proj_data.proj_ply_write
            ply_write = list(map(tuple, ply_write))
            temps = proj_data.temps
            cam_pos = proj_data.cam[0]
            lookat = proj_data.cam[1]
            # viz the stl file
            three_mesh, outlines = create_tri_mesh(stl_xyzs)
            # viz the projected points
            mn_temp = min(temps)
            mx_temp = max(temps)
            change_color_bar(mn_temp, mx_temp)
            pts_colors = rgb_falsecolors(temps, mn_temp, mx_temp)
            threejs_pts_proj = viz_pts_color(ply_xyzs_viz, pts_colors, size=0.05)
            # viz the sensor pos
            sphere = create_sphere(0.1, 10, 10, r = 1, g = 0, b = 0)
            sphere.position.set(sensor_pos_zxy[0], sensor_pos_zxy[1], sensor_pos_zxy[2])

            world.add(outlines)
            world.add(threejs_pts_proj)
            world.add(sphere)
            
            scene.remove(init_edges)

            camera.position.set(cam_pos[0], cam_pos[1], cam_pos[2])
            camera.lookAt(lookat)
            scene.add(world)
            worker.terminate()
            loading_dialog.close()
            
            global PROJECTED_PTS
            dtype_val = [('x', 'f4'), ('y', 'f4'), ('z', 'f4'), ('temperature', 'f4')]
            projected_ply = write_ply_web(ply_write, dtype_val)
            PROJECTED_PTS = projected_ply
            t2 = perf_counter()
            dur = int((t2 - t1)/60)
            if dur == 0:
                dur = 'less than a minute'
            output_p.textContent = f"Success! Time Elapsed (mins): {dur}"
            
            dl_btn.disabled = False
            dl_msg = document.querySelector("#st-output")
            dl_msg.textContent = 'Refresh to do another projection.'
        else:
            loading_dialog = document.getElementById("loading")
            loading_dialog.showModal()
            change_dialog_text('Please specify STL and PLY file')
            
    except Exception as e:
        change_dialog_text(e)
        print(e)

def downloadFile(*args):
    create_hidden_link(PROJECTED_PTS, f"{PLY_NAME}_projected", 'ply')

if __name__ == "__main__":
    animate()
    add_event_listener(document.getElementById("stgeom-submit"), "click", lambda e: asyncio.create_task(on_pts_submit(e)))
    add_event_listener(document.getElementById("st-download"), "click", downloadFile)