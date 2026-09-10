import rclpy
import numpy as np
from rclpy.node import Node

from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from geometry_msgs.msg import Twist, PoseWithCovarianceStamped, TransformStamped, Pose

import tf_transformations
from tf2_ros import TransformBroadcaster

from .modules.robot_base import RobotDriver

class DriverNode(Node):
    def __init__(self):
        super().__init__("generic_robot_driver")
        
        # Parameters
        self.rate = 50 #50
        self.create_rate(self.rate)
        
        self.declare_parameter('enable_tf_pub', False)
        self.declare_parameter('enable_jointstate_pub', False)
        self.declare_parameter('motor_type', 'hw231')

        self.enable_tf_pub = self.get_parameter('enable_tf_pub').value
        self.enable_jointstate_pub = self.get_parameter('enable_jointstate_pub').value
        self.motor_type = self.get_parameter('motor_type').value

        # Pub & Sub
        self._subcriber_cmdvel = self.create_subscription(Twist, 'cmd_vel', self.callback_cmdvel, 10)
        self._publisher_odom = self.create_publisher(Odometry, 'odom', 10)
        self._publisher_jointstate = self.create_publisher(JointState, 'joint_states', 10)
        
        # TF Broadcaster
        self._tf_broadcaster = TransformBroadcaster(self)

        # Robot
        self.robot = RobotDriver(hz=self.rate, motor_addrs=[0x43, [2, 3], [0, 1]], encoder_addrs=[0x41, 0x40], motor_type=self.motor_type)

        # Loop
        self.timer = self.create_timer( 1 / self.rate, self.timer_callback )
    

    def timer_callback(self):
        current_time = self.get_clock().now().to_msg()

        (x, y), (vx, vth), th = self.robot.get_robot_metadata()
        q = tf_transformations.quaternion_from_euler(0, 0, th)

        if self.enable_tf_pub is True:
            t = TransformStamped()
            t.header.stamp = current_time
            t.header.frame_id = "odom"
            t.child_frame_id = "base_footprint"
            t.transform.translation.x = x
            t.transform.translation.y = y
            t.transform.translation.z = 0.
            t.transform.rotation.x = q[0]
            t.transform.rotation.y = q[1]
            t.transform.rotation.z = q[2]
            t.transform.rotation.w = q[3]
            self._tf_broadcaster.sendTransform(t)

        odom = Odometry()
        odom.header.stamp = current_time
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_footprint"

        pose = Pose()
        pose.position.x = x
        pose.position.y = y
        pose.position.z = 0.
        pose.orientation.x = q[0]
        pose.orientation.y = q[1]
        pose.orientation.z = q[2]
        pose.orientation.w = q[3]
        odom.pose.pose = pose
        odom.pose.covariance = [0.01, 0., 0., 0., 0., 0.,
                                0., 0.01, 0., 0., 0., 0.,
                                0., 0., 0.01, 0., 0., 0.,
                                0., 0., 0., 0.1, 0., 0.,
                                0., 0., 0., 0., 0.1, 0.,
                                0., 0., 0., 0., 0., 0.1]

        twist = Twist()
        twist.linear.x = 0.
        twist.linear.y = vx
        twist.linear.z = 0.
        twist.angular.x = 0.
        twist.angular.y = 0.
        twist.angular.z = 0.
        odom.twist.twist = twist

        self._publisher_odom.publish(odom)

        if self.enable_jointstate_pub is True:
            jointState = JointState()
            jointState.header.stamp = self.get_clock().now().to_msg()
            jointState.name = [
                'l_wheel_joint',
                'r_wheel_joint',
                'r_caster_swivel_joint',
                'l_caster_swivel_joint',
                'r_caster_wheel_joint',
                'l_caster_wheel_joint'
            ]
            jointState.position = [
                self.robot.get_left_motor_encoder_position(),
                self.robot.get_right_motor_encoder_position(),
                0.,
                0.,
                0.,
                0.
            ]
            jointState.velocity = []
            jointState.effort = []
            self._publisher_jointstate.publish(jointState)

    def callback_cmdvel(self, msg):
        self.robot.move([msg.linear.x, -msg.angular.z])

    def stop(self):
        self.robot.stop()

def main(args=None):
    rclpy.init(args=args)

    driver_node = DriverNode()
    rclpy.spin(driver_node)
    driver_node.stop()
    driver_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
