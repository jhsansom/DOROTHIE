# -*- coding: utf-8 -*-

import numpy as np
import string
import json
import math

town3_blank = u'''
  1  2  3  4  5  6  7  8
A    ┏━━━━━╦━━━━━╦━━╦━━┓
B    ┃     ┃     ┃  ┃  ┃
C ┏━━╬━━━━━╬━━━━━╬━━╣  ┃
D ┃  ┃     ┃     ┃  ┃  ┃
E ┃  ┃     ┃     ╠━━╣  ┃
F ┃  ┃  ┏━━╩━━┓  ┃  ┃  ┃
G ╠━╦╬━━╣     ╠━━╩━━╩━━╣
H ┃ ┃┃  ┗━━╦━━┛        ┃
I ╠━┛┃     ┃     ╞━━╦━━╣
J ┃  ┃     ┃        ┃  ┃
K ╚━━╬━━━━━╬━━━━━━━━┛  ┃
L    ┃  ┏━━╣           ┃
M    ┗━━╩━━╩━━━━━━━━━━━┛
'''

intersection_ids = {
    655: 'A4',
    576: 'A6',
    498: 'A7',

    730: 'C2',
    1221: 'C4',
    356: 'C6',
    1696: 'C7',

    1794: 'E6',
    1441: 'E7',

    1820: 'G1',
    861: 'G2',
    475: 'G6',
    1168: 'G7',
    1135: 'G8',

    # Circle, clockwise
    1469: 'G3', 
    1682: 'F4',
    1082: 'F4',
    1205: 'G5',
    1191: 'G5',
    1736: 'H4',
    1654: 'H4',
    
    1901: 'I1',
    1427: 'I6',
    1038: 'I7',
    1352: 'I8',

    1669: 'K1',
    238: 'K2',
    103: 'K4',
    # Technically should be G2 and F-G 3
    1019: 'L4',

    1932: 'M3',
    82: 'M4'
}

concavities = {
    ('A7', 'G8') : 'DOWN',
    ('C2', 'A4') : 'DOWN',
    ('F4', 'G5') : 'DOWN',
    ('G1', 'C2') : 'DOWN',
    ('G3', 'F4') : 'DOWN',
    ('G3', 'H4') : 'UP',
    ('H4', 'G5') : 'UP',
    ('I5', 'G2') : 'UP',
    ('K2', 'M3') : 'UP',
    ('K4', 'I7') : 'UP',
    ('M3', 'L4') : 'DOWN',
    ('M4', 'I8') : 'UP'
}

'''
    Translates a coordinate in "battleship coordinates" (e.g. "B4")
    to an (i,j) representation that can be inserted in the text map
'''
def get_intersection_coordinates(battleship_rep):
    letters = [l for l in battleship_rep]
    row = ord(letters[0]) - 63
    col = (int(letters[1]) - 1) * 3 + 2

    return [row, col]


class TownMap:

    def __init__(self, town_name):
        self.town_name = town_name

        self.load_blank_map()

        town_data_filepath = './' + self.town_name + '.json'
        with open(town_data_filepath, 'r') as f:
            self.town_data = json.load(f)

    
    def load_blank_map(self):
        text_maps = {
            'Town03' : town3_blank
        }

        self.text_map = text_maps[self.town_name]

    def add_landmark(self, landmarks):
        self.landmark_key = {}
        for i, landmark in enumerate(landmarks):
            landmark_name = landmark['name']
            landmark_loc = landmark['wp']['waypoint_Transform']['Location']
            landmark_loc = (landmark_loc['x'], landmark_loc['y'])
            landmark_pos = self.get_absolute_position(landmark_loc)
            letter = string.ascii_uppercase[i]
            self.landmark_key[landmark_name] = letter
            try:
                self.insert_char(letter, landmark_pos)
            except Exception as e:
                print(e) # TODO: not sure why some coordinates are way off-map

    def get_absolute_position(self, coor):
        dist1 = 100000 # nearest node
        dist2 = 100000 # second nearest node
        node1 = None
        node2 = None
        id1 = None
        id2 = None
        for node in self.town_data['meta_map']['nodes']:
            id_num = node['id']
            x = node['x_axis']
            y = node['y_axis']
            dist_sq = (coor[0] - x)**2 + (coor[1] - y)**2

            if dist_sq < dist2:
                if dist_sq < dist1:
                    dist2 = dist1
                    node2 = node1
                    id2 = id1
                    node1 = (x, y)
                    dist1 = dist_sq
                    id1 = intersection_ids[id_num]
                else:
                    node2 = (x, y)
                    dist2 = dist_sq
                    id2 = intersection_ids[id_num]

        node1_text_coor = get_intersection_coordinates(id1)
        node2_text_coor = get_intersection_coordinates(id2)

        x_coor = int(node1_text_coor[0] + round((coor[0] - node1[0]) / (node2[0] - node1[0]) * (node2_text_coor[0] - node1_text_coor[0])))
        y_coor = int(node1_text_coor[1] + round((coor[1] - node1[1]) / (node2[1] - node1[1]) * (node2_text_coor[1] - node1_text_coor[1])))

        return (x_coor, y_coor)


    def get_road_position(self, road_id):
        intersections = []
        for node in self.town_data['meta_map']['nodes']:
            if road_id in node['neighbor_edge']:
                intersection = intersection_ids[node['id']]
                intersections.append(intersection)

        i1 = get_intersection_coordinates(intersections[0])
        i2 = get_intersection_coordinates(intersections[1])

        # Re-arrange so that intersection with smaller column num
        # comes first in tuple
        if intersections[0][1] <= intersections[1][1]:
            intersections = (intersections[0], intersections[1])
            coors = [i1, i2]
        else:
            intersections = (intersections[1], intersections[0])
            coors = [i2, i1]

        # Test for equality along either dimension
        diff = np.subtract(coors[1], coors[0])
        if coors[0][0] == coors[1][0] or coors[0][1] == coors[1][1]:
            diff = np.ceil(diff / 2).astype(int)
        else:
            concavity = concavities[intersections]
            if concavity == 'UP':
                if abs(diff[0]) > abs(diff[1]):
                    diff[1] = math.ceil(diff[1] / 2)
                else:
                    diff[0] = math.ceil(diff[0] / 2)
            else:
                if abs(diff[0]) > abs(diff[1]):
                    diff[0] = math.ceil(diff[0] / 2)
                    diff[1] = 0
                else:
                    diff[1] = math.ceil(diff[1] / 2)
                    diff[0] = 0

        position = np.add(coors[0], diff)

        return position


    def insert_char(self, char, pos):

        # Get coordinate position
        i = pos[0] # row number, 0-indexed
        j = pos[1] # column number, 0-indexed

        # Split apart map and insert char
        text_map_split = self.text_map.splitlines()
        line_to_modify = text_map_split[i]
        split_line = [c for c in line_to_modify]
        split_line[j] = char

        # Recombine map
        text_map_split[i] = "".join(split_line)
        new_map = '\n'.join(text_map_split)
        
        self.text_map = new_map
