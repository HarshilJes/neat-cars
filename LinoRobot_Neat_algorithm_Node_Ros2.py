import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geographic_msgs.msg import Twist
import math
from checkpoint import *
import neat
import os

input=[]

NEAT_CONFIG_PATH = "config.txt"

# Define a MinimalSubscriber class that inherits from Node
class Rplidar_Subscriber(Node):

    def __init__(self):
        # Initialize the node with the name 'minimal_subscriber'
        super().__init__('rplidar_subscriber')
        # Define the interval for reporting obstacle distances (in degrees)
        self.REPORT_INTERVAL = 45
        self.input=[0,0,0,0,0]
        # Create a subscription to the 'topic' topic
        # The subscription will use the String message type
        # The listener_callback function will be called when a message is received
        # The queue size is set to 10
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.listener_callback,
            10)
        
        # Prevent unused variable warning (not strictly necessary, but good practice)
        self.subscription  

    def process_input(self):
        return self.input

    def process_data(self,angle_degrees, distance):
        # Print the angle and distance of the obstacle if the distance is less than 1 meter
        if distance > 0.28 and distance < 0.8:
            self.get_logger().info("Angle: {:.2f} degrees, Distance: {:.2f} meters".format(angle_degrees, distance))
     
    # Define the callback function that will be called when a message is received
    def listener_callback(self, msg):
        # Get the number of laser scan points
        num_points = len(msg.ranges)

        # Calculate the angle increment between scan points
        angle_increment = msg.angle_increment

        # Calculate the minimum angle of the laser scan
        # min_angle = msg.angle_min
        min_angle=0

        # Initialize the angle for the first report interval
        report_angle = 0

        # # Iterate through the laser scan points
        # for i in range(num_points):
        #     # Calculate the angle of the current laser scan point
        #     angle = min_angle + i * angle_increment

        #     # Ensure angle is between 0 and 360 degrees
        #     angle_degrees = round(math.degrees(angle) % 360)

        #     # Check if the current angle is within the next report interval
        #     if angle_degrees >= report_angle and angle_degrees < report_angle + self.REPORT_INTERVAL:
        #         # Get the distance measurement at the current angle
        #         distance = msg.ranges[i]

        #         # Process the distance and angle data as needed
        #         process_data(angle_degrees, distance)
        
        # # Iterate through the laser scan points
        # for i in range(num_points):
        #     # Calculate the angle of the current laser scan point
        #     angle = min_angle + i * angle_increment

        #     # Ensure angle is between 0 and 360 degrees
        #     angle_degrees = round(math.degrees(angle) % 360)

        self.angle=[315,270,1,45,90]

        for j in self.angle:
            self.input[self.angle.index(j)]=msg.ranges[j]

                # Process the distance and angle data as needed

            # # Update the angle for the next report interval
            # report_angle += self.REPORT_INTERVAL

            # # If report angle exceeds 360 degrees, wrap around to 0
            # if report_angle >= 360:
            #     report_angle = 0

    
class Action:
    TURN_LEFT = 0
    TURN_RIGHT = 1
    ACCELERATE = 2
    BRAKE = 3


class bot_control:
    def __init__(self):

        # Call the initializer of the Node class with the name 'minimal_publisher'
        super().__init__('Cmd_vel_publisher')
        
        self.Pose=Twist()
        # Create a publisher that publishes String messages to the 'topic' topic with a queue size of 10
        self.publisher= self.create_publisher(self.Pose, '/cmd_vel', 10)

        self.NEAT_CONFIG_PATH = NEAT_CONFIG_PATH
        
        # Load neat config file
        config = neat.config.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            self.NEAT_CONFIG_PATH
        )

        self.file_name = 'Best_generation'

        # Get the current working directory
        self.current_directory = os.getcwd()

        # Check if the file exists in the current working directory
        self.file_path = os.path.join(self.current_directory, self.file_name)
         # Create population
        self.population = neat.Population(config)

        if os.path.exists(self.file_path):
            checkpoint=Checkpointer()
            filename='Best_generation'
            self.population.Population=checkpoint.restore_checkpoint(filename)
            print("Trained genome imported from checkpoint")
        else:    
            print("Can't detect the trained genome")
    def control_output(self,input[]):
        Best_Genome=self.population.best_genome
        self.net=neat.nn.feed_forward(Best_Genome)

        # Activate the neural network and get the output from the car_data (input)
        self.output=self.net.activate(input)        
        # Output gets treated and the car is updated in the next lines
        choice = self.output.index(max(self.output))


        # 0: Left
        if choice == Action.TURN_LEFT:
            self.Pose.angular.z=0.1

        # 1: Right
        elif choice == Action.TURN_RIGHT:
            self.Pose.angular.z=-0.1 

        # 2: Accelerate
        elif choice == Action.ACCELERATE:
            self.Pose.linear.x= 0.5

        # 3: Brake
        elif choice == Action.BRAKE:
            self.Pose.linear.x=0

        self.publisher.publish(self.Pose)


if __name__ =='__main__':
    # Initialize the rclpy library
    rclpy.init
        
    # Create an instance of the Rpliadr_subscriber node
    rplidar_subscriber = Rplidar_Subscriber()


    # Keep the node running to listen for messages
    rclpy.spin(rplidar_subscriber)

    Bot_control=bot_control()
    Bot_control.control_output(rplidar_subscriber.process_input)