# endcoding: utf-8
import math
import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
from funfluid.lbm.core.buff import Buff
from funfluid.lbm.core.speed_nb import *
from funfluid.utils.log import logger


class Obstacle:
    """
    障碍物
    """

    def __init__(self, polygon, area, boundary, ibb, tag):
        self.polygon = polygon
        self.area = area
        self.boundary = boundary
        self.ibb = ibb
        self.tag = tag


class BaseDefine:
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', 'lattice')
        self.x_min = kwargs.get('x_min', 0.0)
        self.x_max = kwargs.get('x_max', 1.0)
        self.y_min = kwargs.get('y_min', 0.0)
        self.y_max = kwargs.get('y_max', 1.0)
        self.nx = kwargs.get('nx', 100)
        self.ny = kwargs.get('ny', self.nx)
        self.tau_lbm = kwargs.get('tau_lbm', 1.0)
        self.dx = kwargs.get('dx', 1.0)
        self.dt = kwargs.get('dt', 1.0)
        self.Cx = kwargs.get('Cx', self.dx)
        self.Ct = kwargs.get('Ct', self.dt)
        self.Cr = kwargs.get('Cr', 1.0)
        self.Cn = kwargs.get('Cn', self.Cx ** 2 / self.Ct)
        self.Cu = kwargs.get('Cu', self.Cx / self.Ct)
        self.Cf = kwargs.get('Cf', self.Cr * self.Cx ** 2 / self.Ct)
        self.dpi = kwargs.get('dpi', 100)
        self.u_lbm = kwargs.get('u_lbm', 0.05)
        self.L_lbm = kwargs.get('L_lbm', 100.0)
        self.nu_lbm = kwargs.get('nu_lbm', 0.01)
        self.Re_lbm = kwargs.get('Re_lbm', 100.0)
        self.rho_lbm = kwargs.get('rho_lbm', 1.0)
        self.IBB = kwargs.get('IBB', False)
        self.stop = kwargs.get('stop', 'it')
        self.t_max = kwargs.get('t_max', 1.0)
        self.it_max = kwargs.get('it_max', 1000)
        self.obs_cv_ct = kwargs.get('obs_cv_ct', 1.0e-1)
        self.obs_cv_nb = kwargs.get('obs_cv_nb', 500)

        # Other parameters
        self.output_it = 0
        self.lx = self.nx - 1
        self.ly = self.ny - 1
        self.q = 9
        self.Cs = 1.0 / math.sqrt(3.0)

        # Output dirs
        time = datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
        self.results_dir = './results/'
        self.output_dir = self.results_dir + str(time) + '/'
        self.png_dir = self.output_dir + './png/'

        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        if not os.path.exists(self.png_dir):
            os.makedirs(self.png_dir)

        # TRT parameters
        self.tau_p_lbm = self.tau_lbm
        self.lambda_trt = 1.0 / 4.0  # Best for stability
        self.tau_m_lbm = self.lambda_trt / (self.tau_p_lbm - 0.5) + 0.5
        self.om_p_lbm = 1.0 / self.tau_p_lbm
        self.om_m_lbm = 1.0 / self.tau_m_lbm
        self.om_lbm = 1.0 / self.tau_lbm

        # D2Q9 Velocities
        self.c = np.array([[0, 0], [1, 0], [-1, 0], [0, 1],
                           [0, -1], [1, 1], [-1, -1], [-1, 1], [1, -1]])

        # Weights
        # Cardinal values, then extra-cardinal values, then central value
        idx_card = [np.linalg.norm(ci) < 1.1 for ci in self.c]
        idx_extra_card = [np.linalg.norm(ci) > 1.1 for ci in self.c]

        self.w = np.ones(self.q)
        self.w[np.asarray(idx_card)] = 1. / 9.
        self.w[np.asarray(idx_extra_card)] = 1. / 36.
        self.w[0] = 4. / 9.

        # Array for bounce-back
        self.ns = np.array([0, 2, 1, 4, 3, 6, 5, 8, 7])

        # Density arrays
        self.g = np.zeros((self.q, self.nx, self.ny))
        self.g_eq = np.zeros((self.q, self.nx, self.ny))
        self.g_up = np.zeros((self.q, self.nx, self.ny))

        # Boundary conditions
        self.u_left = np.zeros((2, self.ny))
        self.u_right = np.zeros((2, self.ny))
        self.u_top = np.zeros((2, self.nx))
        self.u_bot = np.zeros((2, self.nx))
        self.rho_right = np.zeros(self.ny)

        # Lattice array is oriented as follows :
        # +x     = left-right
        # +y     = bottom-top
        # origin = bottom left
        self.lattice = np.zeros((self.nx, self.ny))

        # Physical fields
        self.rho = np.ones((self.nx, self.ny))
        self.u = np.zeros((2, self.nx, self.ny))

        # Obstacles
        self.obstacles = []

        # Iterating and stopping
        self.it = 0
        self.compute = False
        self.drag_buff = Buff('drag', self.dt, self.obs_cv_ct, self.obs_cv_nb, self.output_dir)
        self.lift_buff = Buff('lift', self.dt, self.obs_cv_ct, self.obs_cv_nb, self.output_dir)

        # Printings
        logger.info('')

        info = f"""
####################################
### LBM solver ###
####################################
##### Computation parameters')
### u_lbm      = {self.u_lbm:f}
### L_lbm      = {self.L_lbm:f}
### nu_lbm     = {self.nu_lbm:f}
### Re_lbm     = {self.Re_lbm:f}
### tau_p_lbm  = {self.tau_p_lbm:f}
### tau_m_lbm  = {self.tau_m_lbm:f}
### dt         = {self.dt:f}
### dx         = {self.dx:f}
### nx         = {self.nx}
### ny         = {self.ny}
### IBB        = {self.IBB}
####################################
            """
        logger.info(info)

    def macro(self):
        """
        Compute macroscopic fields
        Compute density
        """
        self.rho[:, :] = np.sum(self.g[:, :, :], axis=0)

        # Compute velocity
        self.u[0, :, :] = np.tensordot(self.c[:, 0], self.g[:, :, :], axes=(0, 0)) / self.rho[:, :]
        self.u[1, :, :] = np.tensordot(self.c[:, 1], self.g[:, :, :], axes=(0, 0)) / self.rho[:, :]

    def equilibrium(self):
        """
        Compute equilibrium state
        """
        nb_equilibrium(self.u, self.c, self.w, self.rho, self.g_eq)

    # Collision and streaming
    def collision_stream(self):
        nb_col_str(self.g, self.g_eq, self.g_up, self.om_p_lbm, self.om_m_lbm, self.c, self.ns,
                   self.nx, self.ny,
                   self.lx, self.ly)


class Condition(BaseDefine):
    def __init__(self, *args, **kwargs):
        super(Condition, self).__init__(*args, **kwargs)

    # Zou-He right wall pressure b.c.
    def zou_he_right_wall_pressure(self):
        nb_zou_he_right_wall_pressure(self.lx, self.ly, self.u,
                                      self.rho_right, self.u_right,
                                      self.rho, self.g)

    def zou_he_wall_velocity(self):
        self.zou_he_bottom_wall_velocity()
        self.zou_he_left_wall_velocity()
        self.zou_he_right_wall_velocity()
        self.zou_he_top_wall_velocity()

    def zou_he_corner_velocity(self):
        self.zou_he_bottom_left_corner()
        self.zou_he_top_left_corner()
        self.zou_he_top_right_corner()
        self.zou_he_bottom_right_corner()

    def zou_he_left_wall_velocity(self):
        """Zou-He left wall velocity b.c."""
        nb_zou_he_left_wall_velocity(self.lx, self.ly, self.u, self.u_left, self.rho, self.g)

    def zou_he_right_wall_velocity(self):
        """Zou-He right wall velocity b.c."""
        nb_zou_he_right_wall_velocity(self.lx, self.ly, self.u, self.u_right, self.rho, self.g)

    def zou_he_top_wall_velocity(self):
        """Zou-He no-slip top wall velocity b.c."""
        nb_zou_he_top_wall_velocity(self.lx, self.ly, self.u, self.u_top, self.rho, self.g)

    def zou_he_bottom_wall_velocity(self):
        """Zou-He no-slip bottom wall velocity b.c."""
        nb_zou_he_bottom_wall_velocity(self.lx, self.ly, self.u, self.u_bot, self.rho, self.g)

    def zou_he_bottom_left_corner(self):
        """Zou-He bottom left corner"""
        nb_zou_he_bottom_left_corner_velocity(self.lx, self.ly, self.u, self.rho, self.g)

    def zou_he_top_left_corner(self):
        """Zou-He top left corner"""
        nb_zou_he_top_left_corner_velocity(self.lx, self.ly, self.u, self.rho, self.g)

    def zou_he_top_right_corner(self):
        """Zou-He top right corner"""
        nb_zou_he_top_right_corner_velocity(self.lx, self.ly, self.u, self.rho, self.g)

    def zou_he_bottom_right_corner(self):
        """Zou-He bottom right corner"""
        nb_zou_he_bottom_right_corner_velocity(self.lx, self.ly, self.u, self.rho, self.g)


class Lattice(Condition):
    def __init__(self, *args, **kwargs):
        super(Lattice, self).__init__(*args, **kwargs)

    # Compute drag and lift
    def drag_lift(self, obs, R_ref, U_ref, L_ref):
        Cx, Cy = nb_drag_lift(self.obstacles[obs].boundary, self.ns, self.c, self.g_up, self.g, R_ref, U_ref, L_ref)

        return Cx, Cy

    # Handle drag/lift buffers
    def add_buff(self, Cx, Cy, it):
        """
        Add to buffer and check for convergence
        """
        self.drag_buff.add(Cx)
        self.lift_buff.add(Cy)

        avg_Cx, dcx = self.drag_buff.mv_avg()
        avg_Cy, dcy = self.lift_buff.mv_avg()

        # Write to file
        filename = self.output_dir + 'drag_lift'
        with open(filename, 'a') as f:
            f.write('{} {} {} {} {} {} {}\n'.format(it * self.dt, Cx, Cy, avg_Cx, avg_Cy, dcx, dcy))

    # Obstacle halfway bounce-back no-slip b.c.
    def bounce_back_obstacle(self, obs):
        nb_bounce_back_obstacle(self.IBB, self.obstacles[obs].boundary,
                                self.ns, self.c, self.obstacles[obs].ibb,
                                self.g_up, self.g, self.u, self.lattice)

    def output_fields(self, it, freq, *args, **kwargs):
        """Output 2D flow amplitude"""
        # Handle inputs
        u_norm = kwargs.get('u_norm', True)
        u_ctr = kwargs.get('u_ctr', False)
        u_stream = kwargs.get('u_stream', True)

        # Exit if no plotting
        if it % freq != 0:
            return

        # Compute norm
        v = np.sqrt(self.u[0, :, :] ** 2 + self.u[1, :, :] ** 2)

        # Mask obstacles
        v[np.where(self.lattice > 0.0)] = -1.0
        vm = np.ma.masked_where((v < 0.0), v)
        vm = np.rot90(vm)

        # Plot u norm
        if u_norm:
            plt.clf()
            fig, ax = plt.subplots(figsize=plt.figaspect(vm))
            fig.subplots_adjust(0, 0, 1, 1)
            plt.imshow(vm,
                       cmap='RdBu_r',
                       vmin=0,
                       vmax=1.5 * self.u_lbm,
                       interpolation='spline16')

            filename = self.png_dir + 'u_norm_' + str(self.output_it) + '.png'
            plt.axis('off')
            plt.savefig(filename,
                        dpi=self.dpi)
            plt.close()

        # Plot u contour
        if u_ctr:
            plt.clf()
            fig, ax = plt.subplots(figsize=plt.figaspect(vm))
            fig.subplots_adjust(0, 0, 1, 1)
            x = np.linspace(0, 1, self.nx)
            y = np.linspace(0, 1, self.ny)
            ux = self.u[0, :, :].copy()
            uy = self.u[1, :, :].copy()
            uy = np.rot90(uy)
            ux = np.rot90(ux)
            uy = np.flipud(uy)
            ux = np.flipud(ux)
            vm = np.sqrt(ux ** 2 + uy ** 2)
            plt.contour(x, y, vm, cmap='RdBu_r',
                        vmin=0.0, vmax=1.5 * self.u_lbm)
            filename = self.png_dir + 'u_ctr_' + str(self.output_it) + '.png'
            plt.axis('off')
            plt.savefig(filename,
                        dpi=self.dpi)
            plt.close()

        # Plot u streamlines
        # The outputted streamplot is rotated and flipped...
        if u_stream:
            plt.clf()
            fig, ax = plt.subplots(figsize=plt.figaspect(vm))
            fig.subplots_adjust(0, 0, 1, 1)
            ux = self.u[0, :, :].copy()
            uy = self.u[1, :, :].copy()
            uy = np.rot90(uy)
            ux = np.rot90(ux)
            uy = np.flipud(uy)
            ux = np.flipud(ux)
            vm = np.sqrt(ux ** 2 + uy ** 2)
            vm = np.rot90(vm)
            x = np.linspace(0, 1, self.nx)
            y = np.linspace(0, 1, self.ny)
            u = np.linspace(0, 1, 100)
            g = np.meshgrid(u, u)
            str_pts = list(zip(*(x.flat for x in g)))
            plt.streamplot(x, y, ux, uy,
                           linewidth=1.5,
                           color=uy,
                           cmap='RdBu_r',
                           arrowstyle='-',
                           start_points=str_pts,
                           density=3)

            filename = self.output_dir + 'u_stream.png'
            plt.axis('off')
            plt.savefig(filename,
                        dpi=self.dpi)
            plt.close()

        # Update counter
        self.output_it += 1

    def add_obstacle(self, polygon, tag):
        """Add obstacle"""
        # Initial print
        print('### Obstacle ', str(tag))

        # Compute polygon bnds
        poly_bnds = np.zeros(4)
        poly_bnds[0] = np.amin(polygon[:, 0])
        poly_bnds[1] = np.amax(polygon[:, 0])
        poly_bnds[2] = np.amin(polygon[:, 1])
        poly_bnds[3] = np.amax(polygon[:, 1])

        # Declare lattice arrays
        obstacle = np.empty((0, 2), dtype=int)
        boundary = np.empty((0, 3), dtype=int)
        ibb = np.empty(1, dtype=float)

        # Fill lattice
        for i in range(self.nx):
            for j in range(self.ny):
                pt = self.lattice_coords(i, j)

                # Check if pt is inside polygon bbox
                if ((pt[0] > poly_bnds[0]) and
                        (pt[0] < poly_bnds[1]) and
                        (pt[1] > poly_bnds[2]) and
                        (pt[1] < poly_bnds[3])):

                    if self.is_inside(polygon, pt):
                        self.lattice[i, j] = tag
                        obstacle = np.append(obstacle, np.array([[i, j]]), axis=0)

        # Printings
        print('# ' + str(obstacle.shape[0]) + ' locations in obstacle')

        # Build boundary of obstacle, i.e. 1st layer of fluid
        for k in range(len(obstacle)):
            i = obstacle[k, 0]
            j = obstacle[k, 1]

            for q in range(1, 9):
                qb = self.ns[q]
                cx = self.c[q, 0]
                cy = self.c[q, 1]
                ii = i + cx
                jj = j + cy

                if not self.lattice[ii, jj]:
                    boundary = np.append(boundary, np.array([[ii, jj, qb]]), axis=0)

        # Some cells were counted multiple times, unique-sort them
        boundary = np.unique(boundary, axis=0)

        # Printings
        print('# ' + str(boundary.shape[0]) + ' locations on boundary')

        # Compute lattice-boundary distances if IBB is True
        if self.IBB:
            for k in range(len(boundary)):
                i = boundary[k, 0]
                j = boundary[k, 1]
                q = boundary[k, 2]
                pt = self.lattice_coords(i, j)
                x = polygon[:, 0] - pt[0]
                y = polygon[:, 1] - pt[1]
                dist = np.sqrt(np.square(x) + np.square(y))
                mpt = np.argmin(dist)
                mdst = dist[mpt] / (self.dx * np.linalg.norm(self.c[q]))
                ibb = np.append(ibb, mdst)

        # Check area of obstacle
        area = 0.0
        for i in range(self.nx):
            for j in range(self.ny):
                if self.lattice[i, j] == tag:
                    area += self.dx ** 2

        # Printings
        print('# Area = ' + '{:f}'.format(area))

        # Add obstacle
        obs = Obstacle(polygon, area, boundary, ibb, tag)
        self.obstacles.append(obs)

        # Last print
        print('')

    def lattice_coords(self, i, j):
        """Get lattice coordinates from integers"""
        # Compute and return the coordinates of the lattice node (i,j)
        dx = (self.x_max - self.x_min) / (self.nx - 1)
        dy = (self.y_max - self.y_min) / (self.ny - 1)
        x = self.x_min + i * dx
        y = self.y_min + j * dy

        return [x, y]

    def is_inside(self, poly, pt):
        """Determine if a pt is inside or outside a closed polygon"""
        # Initialize
        j = len(poly) - 1
        odd_nodes = False

        # Check if point is inside or outside
        # This is a valid algorithm for any non-convex polygon
        for i in range(len(poly)):
            if (((poly[i, 1] < pt[1] <= poly[j, 1]) or
                 (poly[j, 1] < pt[1] <= poly[i, 1])) and
                    (poly[i, 0] < pt[0] or poly[j, 0] < pt[0])):

                # Compute slope
                slope = (poly[j, 0] - poly[i, 0]) / (poly[j, 1] - poly[i, 1])

                # Check side
                if (poly[i, 0] + (pt[1] - poly[i, 1]) * slope) < pt[0]:
                    odd_nodes = not odd_nodes

            # Increment
            j = i

        return odd_nodes

    def generate_image(self):
        """Generate lattice image"""
        # Add obstacle border
        lat = self.lattice.copy()
        lat = lat.astype(float)

        for obs in range(len(self.obstacles)):
            for k in range(len(self.obstacles[obs].boundary)):
                i = self.obstacles[obs].boundary[k, 0]
                j = self.obstacles[obs].boundary[k, 1]
                lat[i, j] = -1.0

        # Plot and save image of lattice
        filename = self.output_dir + self.name + '.png'

        plt.imsave(filename,
                   np.rot90(lat),
                   vmin=-1.0,
                   vmax=1.0)

    def set_inlet_poiseuille(self, u_lbm, rho_lbm, it, sigma):
        """Set inlet poiseuille fields"""
        self.u_left[:] = 0.0
        self.u_right[:] = 0.0
        self.u_top[:] = 0.0
        self.u_bot[:] = 0.0
        self.rho_right[:] = rho_lbm

        for j in range(self.ny):
            pt = self.lattice_coords(0, j)
            self.u_left[:, j] = u_lbm * self.poiseuille(pt, it, sigma)

    def set_full_poiseuille(self, u_lbm, rho_lbm):
        """Set full poiseuille fields"""
        self.u_left[:] = 0.0
        self.u_right[:] = 0.0
        self.u_top[:] = 0.0
        self.u_bot[:] = 0.0
        self.rho_right[:] = rho_lbm

        for j in range(self.ny):
            for i in range(self.nx):
                pt = self.lattice_coords(i, j)
                u = u_lbm * self.poiseuille(pt, 1, 1.0e-10)
                self.u_left[:, j] = u
                self.u[:, i, j] = u

    def set_cavity(self, ut, ub=0.0, ul=0.0, ur=0.0):
        """Set driven cavity fields"""
        lx = self.lx
        ly = self.ly

        self.u_left[:] = 0.0
        self.u_right[:] = 0.0
        self.u_top[:] = 0.0
        self.u_bot[:] = 0.0

        self.u_top[0, :] = ut
        self.u_bot[0, :] = ub
        self.u_left[1, :] = ul
        self.u_right[1, :] = ur

        self.u[0, :, ly] = self.u_top[0, :]
        self.u[1, :, ly] = self.u_top[1, :]
        self.u[0, :, 0] = self.u_bot[0, :]
        self.u[1, :, 0] = self.u_bot[1, :]
        self.u[0, 0, :] = self.u_left[0, :]
        self.u[1, 0, :] = self.u_left[1, :]
        self.u[0, lx, :] = self.u_right[0, :]
        self.u[1, lx, :] = self.u_right[1, :]

    def poiseuille(self, pt, it, sigma):
        """Poiseuille flow"""
        x = pt[0]
        y = pt[1]
        H = self.y_max - self.y_min
        u = np.zeros(2)
        u[0] = 4.0 * (self.y_max - y) * (y - self.y_min) / H ** 2

        val = it
        ret = (1.0 - math.exp(-val ** 2 / (2.0 * sigma ** 2)))
        u *= ret

        return u

    def poiseuille_error(self, u_lbm):
        """Poiseuille error in the middle of the domain"""
        u_error = np.zeros((2, self.ny))
        nx = math.floor(self.nx / 2)

        for j in range(self.ny):
            pt = self.lattice_coords(nx, j)
            u_ex = self.poiseuille(pt, 1.0e10, 1)
            u = self.u[:, nx, j]

            u_error[0, j] = u[0] / u_lbm
            u_error[1, j] = u_ex[0]

        # Write to file
        filename = self.output_dir + 'poiseuille'
        with open(filename, 'w') as f:
            for j in range(self.ny):
                f.write('{} {} {}\n'.format(j * self.dx,
                                            u_error[0, j],
                                            u_error[1, j]))

    def cavity_error(self, u_lbm):
        """Cavity error in the middle of the domain"""
        ux_error = np.zeros(self.nx)
        uy_error = np.zeros(self.ny)
        nx = math.floor(self.nx / 2)
        ny = math.floor(self.ny / 2)

        for i in range(self.nx):
            uy_error[i] = self.u[1, i, ny] / u_lbm

        for j in range(self.ny):
            ux_error[j] = self.u[0, nx, j] / u_lbm

        # Write to files
        filename = self.output_dir + 'cavity_uy'
        with open(filename, 'w') as f:
            for i in range(self.nx):
                f.write('{} {}\n'.format(i * self.dx, uy_error[i]))
        filename = self.output_dir + 'cavity_ux'
        with open(filename, 'w') as f:
            for j in range(self.ny):
                f.write('{} {}\n'.format(j * self.dx, ux_error[j]))

    def check_stop(self):
        """Check stopping criterion"""
        if self.stop == 'it':
            if self.it > self.it_max:
                self.compute = True
                print('\n')
                print('# Computation ended: it>it_max')

        if self.stop == 'obs':
            if self.drag_buff.obs_cv and self.lift_buff.obs_cv:
                self.compute = True
                print('\n')
                print('# Computation ended: converged')

        self.it += 1
        return self.compute

    def it_printings(self):
        """Iteration printings"""
        if self.stop == 'it':
            print('# it = ' + str(self.it) + ' / ' + str(self.it_max), end='\r')
        if self.stop == 'obs':
            str_d = "{:10.6f}".format(self.drag_buff.obs)
            str_l = "{:10.6f}".format(self.lift_buff.obs)

            print('# it = ' + str(self.it) +
                  ', avg drag =' + str_d + ', avg lift =' + str_l, end='\r')
