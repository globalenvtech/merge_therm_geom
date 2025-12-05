from pyscript import window

from pyscript.js_modules import three as THREE
from pyscript.js_modules.oc import OrbitControls

def get_renderer():
    renderer = THREE.WebGLRenderer.new(antialias=True)
    renderer.shadowMap.enabled = False
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    renderer.shadowMap.needsUpdate = True
    return renderer

def get_scene():
    scene = THREE.Scene.new()
    axes = THREE.AxesHelper.new(5)
    grid = THREE.GridHelper.new(10,10)
    scene.add(axes)
    scene.add(grid)
    return scene 

def get_camera():
    camera = THREE.PerspectiveCamera.new(
        45,
        window.innerWidth / window.innerHeight,
        0.1,
        500000,
    )
    return camera

def get_lights():
    light_back_green = THREE.PointLight.new(0x00FF00, 1, 1000)
    light_back_green.decay = 3.0
    light_back_green.position.set(5, 0, 2)

    light_back_white = THREE.PointLight.new(0xFFFFFF, 5, 1000)
    light_back_white.decay = 20.0
    light_back_white.position.set(5, 0, 2)
    return light_back_green, light_back_white

def get_orbit_ctrl(camera: THREE.PerspectiveCamera, renderer: THREE.WebGLRenderer) -> OrbitControls:
    controls = OrbitControls.new(camera, renderer.domElement)
    controls.enableDamping = True
    controls.dampingFactor = 0.04
    return controls

def viz_pts(positions: list, size: float = 0.03, rgb_color: list = [1,1,1]) -> THREE.Points:
    """
    create threejs point clouds for visualization

    Parameters
    ----------
    positions : list
        a flat list defined as [x1, y1, z1, x2, y2, z2, ... , xn, yn, zn]
    
    size : float, optional
        the size of the points. Default is 0.03

    rgb_color : list, optional
        list[shape(3)] rgb color in a list.

    Returns
    -------
    points : THREE.Points
        threejs points that can be visualize
    """
    poss = window.Float32Array.new(positions)
    geometry = THREE.BufferGeometry.new()
    geometry.setAttribute('position', THREE.BufferAttribute.new(poss, 3))

    material = THREE.PointsMaterial.new(color = THREE.Color.new(rgb_color[0], rgb_color[1], rgb_color[2]), size = size, sizeAttenuation = True)
    points = THREE.Points.new(geometry, material)
    return points

def viz_pts_color(positions: list, colors: list, size: float = 0.03) -> THREE.Points:
    """
    create threejs point clouds for visualization

    Parameters
    ----------
    positions : list
        a flat list defined as [x1, y1, z1, x2, y2, z2, ... , xn, yn, zn]
    
    colors : list
        a flat list defined as [r1, g1, b1, r2, g2, b2, ... , rn, gn, bn]

    size : float, optional
        the size of the points. Default is 0.03

    Returns
    -------
    points : THREE.Points
        threejs points that can be visualize
    """
    positions = window.Float32Array.new(positions)
    colors = window.Float32Array.new(colors)
    geometry = THREE.BufferGeometry.new()
    geometry.setAttribute('position', THREE.BufferAttribute.new(positions, 3))
    geometry.setAttribute('color', THREE.BufferAttribute.new(colors, 3))

    material = THREE.PointsMaterial.new( size = size, sizeAttenuation = True, vertexColors = True)
    points = THREE.Points.new(geometry, material)
    return points

def create_color(r: float, g: float, b: float) -> THREE.Color:
    """
    create threejs color

    Parameters
    ----------
    r : float
        a number between 0-1 specifying the red of rgb 
    
    g : float
        a number between 0-1 specifying the green of rgb 
    
    b : float
        a number between 0-1 specifying the blue of rgb 

    Returns
    -------
    three_color : THREE.Color
        threejs color 
    """
    three_color = THREE.Color.new(r,g,b)
    return three_color

def create_tri_mesh(positions: list, rgb_color: list = [0.8, 0.8, 0.8]) -> THREE.Mesh:
    """
    create threejs color

    Parameters
    ----------
    positions : list
        a flat list with original shape list[shape(n,3,3)], n=ntriangles, each tri has 3 points and each point has 3 vertices. 

    rgb_color : list, optional
        list[shape(3)] rgb color in a list.

    Returns
    -------
    three_mesh : THREE.Mesh
        threejs mesh 
    """
    poss = window.Float32Array.new(positions)
    geometry = THREE.BufferGeometry.new()
    geometry.setAttribute('position', THREE.BufferAttribute.new(poss, 3))
    geometry.computeVertexNormals()

    material = THREE.MeshBasicMaterial.new(color = THREE.Color.new(rgb_color[0], rgb_color[1], rgb_color[2]))
    mesh = THREE.Mesh.new(geometry, material)

    edges = THREE.EdgesGeometry.new(geometry)
    line_material = THREE.LineBasicMaterial.new(color = THREE.Color.new(1,1,1))
    geom_outline = THREE.LineSegments.new(edges, line_material)
    return mesh, geom_outline

def create_grp():
    grp = THREE.Group.new()
    return grp

def create_cube(sx: float = 1, sy: float = 1, sz: float = 1, r: float = 0.5, g: float = 0.5, b: float = 0.5):
    geometry = THREE.BoxGeometry.new(sx, sy, sz)
    material = THREE.MeshBasicMaterial.new(color = THREE.Color.new(r, g, b))
    cube = THREE.Mesh.new(geometry, material)
    # generate the edges of a cube
    edges = THREE.EdgesGeometry.new(geometry)
    line_material = THREE.LineBasicMaterial.new(color = THREE.Color.new(1,1,1))
    cube_edges = THREE.LineSegments.new(edges, line_material)
    
    return cube, cube_edges

def create_sphere(radius: float, width_segs: int, height_segs: int, r: float = 0.5, g: float = 0.5, b: float = 0.5):
    geometry = THREE.SphereGeometry.new(radius, width_segs, height_segs)
    material = THREE.MeshBasicMaterial.new(color = THREE.Color.new(r, g, b))
    sphere = THREE.Mesh.new( geometry, material)
    return sphere