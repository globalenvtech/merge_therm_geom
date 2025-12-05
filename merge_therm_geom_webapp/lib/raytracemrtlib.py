
def separate_rays(rays, nparallel):
    rays_ls = []
    nrays = len(rays)
    interval = nrays/nparallel
    for i in range(nparallel):
        start = int(interval*i)
        end = int(interval*(i+1))
        rays_ls.append(rays[start:end])
    return rays_ls