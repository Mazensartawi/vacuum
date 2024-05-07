import os
import sys
import math

import time

import numpy as np
import matplotlib.pyplot as plt

import time
import RPi.GPIO as GPIO

# Constants
MOTOR_1_PIN_1 = 11
MOTOR_1_PIN_2 = 13
MOTOR_2_PIN_1 = 16
MOTOR_2_PIN_2 = 18
DIRECTION_PIN = 18
PWM_FREQUENCY = 500

do_animation = False

class SpiralSpanningTreeCoveragePlanner:

    # directions array
    directions = []

    def __init__(self, occ_map):
        self.origin_map_height = occ_map.shape[0]
        self.origin_map_width = occ_map.shape[1]

        # original map resolution must be even
        if self.origin_map_height % 2 == 1 or self.origin_map_width % 2 == 1:
            sys.exit('original map width/height must be even \
                in grayscale .png format')

        self.occ_map = occ_map
        self.merged_map_height = self.origin_map_height // 2
        self.merged_map_width = self.origin_map_width // 2

        self.edge = []

    def plan(self, start):
        """plan

        performing Spiral Spanning Tree Coverage path planning

        :param start: the start node of Spiral Spanning Tree Coverage
        """

        visit_times = np.zeros(
            (self.merged_map_height, self.merged_map_width), dtype=int)
        visit_times[start[0]][start[1]] = 1

        # generate route by
        # recusively call perform_spanning_tree_coverage() from start node
        route = []
        self.perform_spanning_tree_coverage(start, visit_times, route)

        path = []
        # generate path from route
        for idx in range(len(route)-1):
            dp = abs(route[idx][0] - route[idx+1][0]) + \
                abs(route[idx][1] - route[idx+1][1])
            if dp == 0:
                # special handle for round-trip path
                path.append(self.get_round_trip_path(route[idx-1], route[idx]))
            elif dp == 1:
                path.append(self.move(route[idx], route[idx+1]))
            elif dp == 2:
                # special handle for non-adjacent route nodes
                mid_node = self.get_intermediate_node(route[idx], route[idx+1])
                path.append(self.move(route[idx], mid_node))
                path.append(self.move(mid_node, route[idx+1]))
            else:
                sys.exit('adjacent path node distance larger than 2')

        return self.edge, route, path, self.directions

    def perform_spanning_tree_coverage(self, current_node, visit_times, route):
        """perform_spanning_tree_coverage

        recursive function for function <plan>

        :param current_node: current node
        """

        def is_valid_node(i, j):
            is_i_valid_bounded = 0 <= i < self.merged_map_height
            is_j_valid_bounded = 0 <= j < self.merged_map_width
            if is_i_valid_bounded and is_j_valid_bounded:
                # free only when the 4 sub-cells are all free
                return bool(
                    self.occ_map[2*i][2*j]
                    and self.occ_map[2*i+1][2*j]
                    and self.occ_map[2*i][2*j+1]
                    and self.occ_map[2*i+1][2*j+1])

            return False

        # counter-clockwise neighbor finding order
        order = [[1, 0], [0, 1], [-1, 0], [0, -1]]

        found = False
        route.append(current_node)
        for inc in order:
            ni, nj = current_node[0] + inc[0], current_node[1] + inc[1]
            if is_valid_node(ni, nj) and visit_times[ni][nj] == 0:
                neighbor_node = (ni, nj)
                self.edge.append((current_node, neighbor_node))
                found = True
                visit_times[ni][nj] += 1
                self.perform_spanning_tree_coverage(
                    neighbor_node, visit_times, route)

        # backtrace route from node with neighbors all visited
        # to first node with unvisited neighbor
        if not found:
            has_node_with_unvisited_ngb = False
            for node in reversed(route):
                # drop nodes that have been visited twice
                if visit_times[node[0]][node[1]] == 2:
                    continue

                visit_times[node[0]][node[1]] += 1
                route.append(node)

                for inc in order:
                    ni, nj = node[0] + inc[0], node[1] + inc[1]
                    if is_valid_node(ni, nj) and visit_times[ni][nj] == 0:
                        has_node_with_unvisited_ngb = True
                        break

                if has_node_with_unvisited_ngb:
                    break

        return route

    def move(self, p, q):
        direction = self.get_vector_direction(p, q)
        self.directions.append(direction)
        print('move direction:', direction)
        print('p:', p)
        # move east
        if direction == 'E':
            p = self.get_sub_node(p, 'SE')
            q = self.get_sub_node(q, 'SW')
        # move west
        elif direction == 'W':
            p = self.get_sub_node(p, 'NW')
            q = self.get_sub_node(q, 'NE')
        # move south
        elif direction == 'S':
            p = self.get_sub_node(p, 'SW')
            q = self.get_sub_node(q, 'NW')
        # move north
        elif direction == 'N':
            p = self.get_sub_node(p, 'NE')
            q = self.get_sub_node(q, 'SE')
        else:
            sys.exit('move direction error...')
        return [p, q]

    def get_round_trip_path(self, last, pivot):
        direction = self.get_vector_direction(last, pivot)
        if direction == 'E':
            return [self.get_sub_node(pivot, 'SE'),
                    self.get_sub_node(pivot, 'NE')]
        elif direction == 'S':
            return [self.get_sub_node(pivot, 'SW'),
                    self.get_sub_node(pivot, 'SE')]
        elif direction == 'W':
            return [self.get_sub_node(pivot, 'NW'),
                    self.get_sub_node(pivot, 'SW')]
        elif direction == 'N':
            return [self.get_sub_node(pivot, 'NE'),
                    self.get_sub_node(pivot, 'NW')]
        else:
            sys.exit('get_round_trip_path: last->pivot direction error.')

    def get_vector_direction(self, p, q):
        # east
        if p[0] == q[0] and p[1] < q[1]:
            return 'E'
        # west
        elif p[0] == q[0] and p[1] > q[1]:
            return 'W'
        # south
        elif p[0] < q[0] and p[1] == q[1]:
            return 'S'
        # north
        elif p[0] > q[0] and p[1] == q[1]:
            return 'N'
        else:
            sys.exit('get_vector_direction: Only E/W/S/N direction supported.')

    def get_sub_node(self, node, direction):
        if direction == 'SE':
            return [2*node[0]+1, 2*node[1]+1]
        elif direction == 'SW':
            return [2*node[0]+1, 2*node[1]]
        elif direction == 'NE':
            return [2*node[0], 2*node[1]+1]
        elif direction == 'NW':
            return [2*node[0], 2*node[1]]
        else:
            sys.exit('get_sub_node: sub-node direction error.')

    def get_interpolated_path(self, p, q):
        # direction p->q: southwest / northeast
        if (p[0] < q[0]) ^ (p[1] < q[1]):
            ipx = [p[0], p[0], q[0]]
            ipy = [p[1], q[1], q[1]]
        # direction p->q: southeast / northwest
        else:
            ipx = [p[0], q[0], q[0]]
            ipy = [p[1], p[1], q[1]]
        return ipx, ipy

    def get_intermediate_node(self, p, q):
        p_ngb, q_ngb = set(), set()

        for m, n in self.edge:
            if m == p:
                p_ngb.add(n)
            if n == p:
                p_ngb.add(m)
            if m == q:
                q_ngb.add(n)
            if n == q:
                q_ngb.add(m)

        itsc = p_ngb.intersection(q_ngb)
        if len(itsc) == 0:
            sys.exit('get_intermediate_node: \
                 no intermediate node between', p, q)
        elif len(itsc) == 1:
            return list(itsc)[0]
        else:
            sys.exit('get_intermediate_node: \
                more than 1 intermediate node between', p, q)

    def visualize_path(self, edge, path, start):
        def coord_transform(p):
            return [2*p[1] + 0.5, 2*p[0] + 0.5]

        if do_animation:
            last = path[0][0]
            trajectory = [[last[1]], [last[0]]]
            for p, q in path:
                distance = math.hypot(p[0]-last[0], p[1]-last[1])
                if distance <= 1.0:
                    trajectory[0].append(p[1])
                    trajectory[1].append(p[0])
                else:
                    ipx, ipy = self.get_interpolated_path(last, p)
                    trajectory[0].extend(ipy)
                    trajectory[1].extend(ipx)

                last = q

            trajectory[0].append(last[1])
            trajectory[1].append(last[0])

            for idx, state in enumerate(np.transpose(trajectory)):
                plt.cla()
                # for stopping simulation with the esc key.
                plt.gcf().canvas.mpl_connect(
                    'key_release_event',
                    lambda event: [exit(0) if event.key == 'escape' else None])

                # draw spanning tree
                plt.imshow(self.occ_map, 'gray')
                for p, q in edge:
                    p = coord_transform(p)
                    q = coord_transform(q)
                    plt.plot([p[0], q[0]], [p[1], q[1]], '-oc')
                sx, sy = coord_transform(start)
                plt.plot([sx], [sy], 'pr', markersize=10)

                # draw move path
                plt.plot(trajectory[0][:idx+1], trajectory[1][:idx+1], '-k')
                plt.plot(state[0], state[1], 'or')
                plt.axis('equal')
                plt.grid(True)
                plt.pause(0.01)

        else:
            # draw spanning tree
            plt.imshow(self.occ_map, 'gray')
            for p, q in edge:
                p = coord_transform(p)
                q = coord_transform(q)
                plt.plot([p[0], q[0]], [p[1], q[1]], '-oc')
            sx, sy = coord_transform(start)
            plt.plot([sx], [sy], 'pr', markersize=10)

            # draw move path
            last = path[0][0]
            for p, q in path:
                distance = math.hypot(p[0]-last[0], p[1]-last[1])
                if distance == 1.0:
                    plt.plot([last[1], p[1]], [last[0], p[0]], '-k')
                else:
                    ipx, ipy = self.get_interpolated_path(last, p)
                    plt.plot(ipy, ipx, '-k')
                plt.arrow(p[1], p[0], q[1]-p[1], q[0]-p[0], head_width=0.2)
                last = q

            plt.show()


def setup_gpio():
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(MOTOR_1_PIN_1, GPIO.OUT)
    GPIO.setup(MOTOR_1_PIN_2, GPIO.OUT)

    GPIO.setup(MOTOR_2_PIN_1, GPIO.OUT)
    GPIO.setup(MOTOR_2_PIN_2, GPIO.OUT)
    return 

def spin_motor():
    setup_gpio()
    
    GPIO.output(MOTOR_1_PIN_1, True)
    GPIO.output(MOTOR_1_PIN_2, False)

    GPIO.output(MOTOR_2_PIN_1, True)
    GPIO.output(MOTOR_2_PIN_2, False)
    return

def get_user_input(prompt):
    while True:
        user_input = input(prompt).strip().upper()
        if user_input in ['L', 'R']:
            return user_input
        print("Invalid input. Please enter 'L' or 'R'.")

def main():
    # dir_path = os.path.dirname(os.path.realpath(__file__))
    # img = plt.imread(os.path.join(dir_path, 'map', 'test_8.png'))
    # STC_planner = SpiralSpanningTreeCoveragePlanner(img)
    # start = (10, 0)
    # edge, route, path, directions = STC_planner.plan(start)
    # # print('start:', start)
    # # print('edge:', edge)
    # # print('route:', route)
    # # print('path:', path)
    # # STC_planner.visualize_path(edge, path, start)

    # print('directions:', directions)

    # #loop through directions
    # num_steps = (339.5 / 360) * 10
    # oldDirection = directions[0]
    # for direction in directions:
    #     print('Ongoing direction:', direction)
    #     if direction == 'N':
    #         spin_motor(True, num_steps, 1)
    #         # spin_motor(True, num_steps, 2)
    #     elif direction == 'S':
    #         spin_motor(True, num_steps, 1)
    #         # spin_motor(False, num_steps, 2)
    #     elif direction == 'E':
    #         spin_motor(True, num_steps, 1)
    #         # spin_motor(False, num_steps, 2)
    #     elif direction == 'W':
    #         spin_motor(False, num_steps, 1)
    #         # spin_motor(True, num_steps, 2)

    # # direction_input = get_user_input('Left or Right (L/R): ')
    # # degree = float(input('Degree: '))
    # # num_steps = (339.5 / 360) * degree
    # # if direction_input == 'L':
    # #     spin_motor(True, num_steps)
    # # else:
    # #     spin_motor(False, num_steps)

    
    setup_gpio()

    # while 1:
        

        # GPIO.output(MOTOR_1_PIN_1, True)
        # GPIO.output(MOTOR_1_PIN_2, False)

        # GPIO.output(MOTOR_2_PIN_1, False)
        # GPIO.output(MOTOR_2_PIN_2, True)
        
        # #GPIO.cleanup()
        # time.sleep(2.2)

        # GPIO.output(MOTOR_1_PIN_1, False)
        # GPIO.output(MOTOR_1_PIN_2, False)

        # GPIO.output(MOTOR_2_PIN_1, False)
        # GPIO.output(MOTOR_2_PIN_2, False)


if __name__ == "__main__":
    main()
