#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

class ReceptionistPatrol(Node):
    def __init__(self):
        super().__init__('receptionist_patrol')
        self.navigator = BasicNavigator()

    def create_pose(self, x, y, z, w):
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.navigator.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.orientation.z = z
        pose.pose.orientation.w = w
        return pose

    def start_patrol(self):
        # --- CONFIGURATION: DEFINE YOUR PATROL POINTS HERE ---
        # Tip: Use RViz "Clicked Point" tool to find these coordinates on your map
        
        # Point A: Toolshaft
        p1 = self.create_pose(x=3.48029, y=2.74027, z=0.529824, w=0.848108)
        
        # Point B: Filament
        p2 = self.create_pose(x=2.37193, y=-0.47493, z=-0.580688, w=0.814126)
        
        # Point C: Meeting room
        p3 = self.create_pose(x=3.78656, y=-2.4799, z=-0.424469, w=0.905442)

        waypoints = [p1, p2, p3]
        # -----------------------------------------------------

        # Wait for Nav2 to be fully active
        self.navigator.waitUntilNav2Active()

        while rclpy.ok():
            self.get_logger().info('Starting Patrol Loop...')
            
            # Send the robot to all waypoints in the list
            self.navigator.followWaypoints(waypoints)

            # Monitor progress
            while not self.navigator.isTaskComplete():
                # --- FUTURE LOGIC PLACEHOLDER ---
                # This is where we will add:
                # if object_detected == "PERSON":
                #     self.navigator.cancelTask()
                # --------------------------------
                pass

            # Check result
            result = self.navigator.getResult()
            if result == TaskResult.SUCCEEDED:
                self.get_logger().info('Patrol Loop Complete! Restarting...')
            elif result == TaskResult.CANCELED:
                self.get_logger().info('Patrol was canceled.')
                break
            elif result == TaskResult.FAILED:
                self.get_logger().info('Patrol failed!')
                break

def main():
    rclpy.init()
    node = ReceptionistPatrol()
    node.start_patrol()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
