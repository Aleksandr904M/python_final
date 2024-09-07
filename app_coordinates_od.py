"""Расчет координат выбранного объекта"""
import numpy as np

def calc_coord(h_object, altitude_drone, theta_vertical, theta_horizontal,
               fov_vertical, fov_horizontal, w_image, h_image, x1, y1, x2, y2,
               latitude_drone, longitude_drone, direction_drone):
    for_vertical_radian = np.radians(fov_vertical)
    for_horizontal_radian = np.radians(fov_horizontal)

    phi_vertical_top = (y1 - h_image/2) / h_image * for_vertical_radian
    phi_horizontal_top = (x1 - w_image/2) / w_image * for_horizontal_radian

    phi_vertical_bottom = (y2 - h_image / 2) / h_image * for_vertical_radian
    phi_horizontal_bottom = (x2 - w_image / 2) / w_image * for_horizontal_radian

    phi_vertical = (phi_vertical_top + phi_vertical_bottom) / 2
    phi_horizontal = (phi_horizontal_top + phi_horizontal_bottom) / 2

    theta_vertical_radian = np.radians(theta_vertical)
    theta_horizontal_radian = np.radians(theta_horizontal)

    D = (altitude_drone - h_object) / np.tan(theta_vertical_radian + phi_vertical)     # расстояние
    R = 6371000                  # радиус Земли

    direction_drone_radian = np.radians(direction_drone)

    delta_latitude = (D * np.cos(theta_horizontal_radian + phi_horizontal + direction_drone_radian)) / R
    latitude_object = latitude_drone + np.degrees(delta_latitude)

    delta_longitude = ((D * np.sin(theta_horizontal_radian + phi_horizontal + direction_drone_radian)) /
                       (R * np.cos(np.radians(latitude_object)))) / R
    longitude_object = longitude_drone + np.degrees(delta_longitude)

    return latitude_object, longitude_object



if __name__ == '__main__':
    h_object = 1.70        # данные для расчета
    altitude_drone = 100
    theta_vertical = -30
    theta_horizontal = 0
    fov_vertical = 45
    fov_horizontal = 60
    w_image = 640
    h_image = 480
    x1, y1, x2, y2 = 300, 200, 360, 240

    latitude_drone = 55.7
    longitude_drone = 37.6
    direction_drone = 45  # направление дрона

    latitude_object, longitude_object = calc_coord(h_object, altitude_drone, theta_vertical,
                                                   theta_horizontal, fov_vertical, fov_horizontal, w_image, h_image,
                                                   x1, y1, x2, y2, latitude_drone, longitude_drone, direction_drone)
    print(f"Обнаружен человек в координате: {latitude_object:.4f}, {longitude_object:.4f}")
