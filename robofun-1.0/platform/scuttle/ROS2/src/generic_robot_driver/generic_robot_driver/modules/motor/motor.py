from abc import abstractmethod

class Motor:
    def __init__(self, i2c_bus_id=1, pins=[0,1], address=0x00, frequency=150):
        self.pins = pins
        self.frequency = frequency
        self.address = address
    
    @abstractmethod
    def set_duty(self, pin, duty):
        pass

    def move_hw231(self, duty):
        # Clamp duty strictly between -1.0 and 1.0
        self.duty = round(sorted((-1.0, float(duty), 1.0))[1], 2)
        current_speed = abs(int(self.duty * 0xFFFF))

        if self.duty == 0:
            # Stop
            self.set_duty(self.pins[0], 0)
            self.set_duty(self.pins[1], 0)
        elif self.duty > 0:
            # Forward: Pin 0 gets PWM speed, Pin 1 is Ground (0)
            self.set_duty(self.pins[0], current_speed)
            self.set_duty(self.pins[1], 0)
        else:
            # Backward: Pin 0 is Ground (0), Pin 1 gets PWM speed
            self.set_duty(self.pins[0], 0)
            self.set_duty(self.pins[1], current_speed)

    def move_md10cr3(self, duty):
        self.duty = round(sorted((-1, float(duty), 1))[1], 2)  # Make sure duty is between -1 and 1
        current_duty = self.duty * 100
        current_speed = abs(int(self.duty * 0xFFFF))
        if current_duty == 0:
            self.set_duty(self.pins[0], 0)
            self.set_duty(self.pins[1], 0)
        else:
            if current_duty > 0:
                self.set_duty(self.pins[0], current_speed)
                self.set_duty(self.pins[1], 0)
            else:
                self.set_duty(self.pins[0], current_speed)
                self.set_duty(self.pins[1], 65535)
                
    def stop(self):
        self.set_duty(self.pins[0], 0)
        self.set_duty(self.pins[1], 0)
