import numpy as np
from scipy.integrate import quad
from math import pi, sin, cos, sqrt


def ellipse_circumference_approx(a, b):
    h = ((a - b) / (a + b)) ** 2
    denom = 10 + sqrt(4 - 3 * h)
    return pi * (a + b) * (1 + 3 * h / denom)


def elliptic_arc_integrand(theta, a, b):
    # https://math.libretexts.org/Bookshelves/Calculus/Calculus_(OpenStax)/ \
    # 11%3A_Parametric_Equations_and_Polar_Coordinates/11.04%3A_Area_and_Arc_Length_in_Polar_Coordinates
    # careful with this
    # https://math.stackexchange.com/questions/433094/how-to-determine-the-arc-length-of-ellipse
    # sqrt((a*sin(t))**2 + (b * cos(t))**2) - t here is the eccentric anomaly, not the polar angle
    # see https://en.wikipedia.org/wiki/Ellipse#Standard_parametric_representation
    # this is combed up sqrt(r**2 + r'**3)
    c = cos(theta)
    s = sin(theta)
    num = pow((b * b * c) ** 2 + (a * a * s) ** 2, 0.5)
    denom = pow((b * c) ** 2 + (a * s) ** 2, 1.5)
    return a * b * num / denom


def find_equipart_angles(a, b, num_arcs):
    # polar angles that divide the ellipse cirumference into num_arcs of equal length
    total_arc = quad(elliptic_arc_integrand, 0, 2 * pi, args=(a, b))[0]
    desired_arc = total_arc / num_arcs
    # print(f" {total_arc:.2f}  {self._allipse_circumference_approx(a, b):.2f}   {num_arcs}  {desired_arc:.2f} ")
    # calculate the arc in small increments, until we pass the best approximation to desired_arc
    angles = []
    num_steps = 1000 * num_arcs
    theta_step = pi / num_steps
    (lower_bound, upper_bound) = (0, 0)
    while lower_bound < 2 * pi:
        for t in range(1, num_steps + 1):
            if t == num_steps: raise Exception("Hmmm, something's wrong here ...")
            upper_bound = lower_bound + t * theta_step
            arc = quad(elliptic_arc_integrand, lower_bound, upper_bound, args=(a, b))[0]
            if arc >= desired_arc:
                angles.append(upper_bound)
                break
        lower_bound = upper_bound

    return angles

def elliptical_mask_main_axes_orientation(height, width, radius_x, radius_y) -> np.ndarray:
    outmatrix = np.zeros((height, width), dtype=np.uint8)

    # Calculate center and half-dimensions
    center_y, center_x = height // 2, width // 2

    # Create coordinate grids
    y, x = np.ogrid[:height, :width]

    # Ellipse equation
    inside_ellipse = ((x - center_x)**2 / radius_x**2 +
                      (y - center_y)**2 / radius_y**2) <= 1

    # Set blue (channel 2) and alpha (channel 3) to 255 inside ellipse
    outmatrix[inside_ellipse] = 255

    return outmatrix

