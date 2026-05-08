# Copyright (C) 2024 Dr. Matthias Kesenheimer - All Rights Reserved.
# You may use, distribute and modify this code under the terms of the GPL3 license.
#
# You should have received a copy of the GPL3 license with this file.
# If not, please write to: info@faultyhardware.de.

class PulseGenerator():
    @micropython.native
    def __init__(self, time_resolution:int = 10, vhigh:float = 1.0, factor:float = 1.0):
        """
        TODO
        """
        self.max_points = 4096
        self.set_time_resolution(time_resolution)
        self.set_calibration(output_voltage_at_minimal_gain=vhigh, calibration_factor=factor)
        self.set_offset(offset=3.3)
        # caching
        self.total_pulse_duration = 0
        self.pulse = []
    @micropython.native
    def get_points_per_ns(self):
        return self.points_per_ns

    @micropython.native
    def set_time_resolution(self, time_resolution:int):
        """
        Set the base time step of the generated pulse in nanoseconds.
        """
        if time_resolution < 1:
            raise Exception("Error: time_resolution must be positive.")
        frequency = int(1_000_000_000 / time_resolution)
        if time_resolution < 8 or frequency > 125_000_000:
            raise Exception("Error: time_resolution too small. Minimum supported value is 8ns.")
        self.time_resolution = time_resolution
        self.frequency = frequency
        self.points_per_ns = 1 / self.time_resolution
        # Invalidate cached pulse buffers when the time grid changes.
        self.total_pulse_duration = 0
        self.pulse = []

    @micropython.native
    def calculate_pulse_number_of_points(self, total_pulse_duration:int) -> int:
        """
        TODO
        """
        pulse_number_of_points = int(total_pulse_duration / self.time_resolution)
        if pulse_number_of_points > self.max_points:
            return self.max_points
        return pulse_number_of_points

    @micropython.native
    def calibration_pulse(self) -> list[int]:
        high = int((0) * self.points_per_volt)
        low = int((0 - self.offset) * self.points_per_volt)
        pulse = [high] * 1000 + [low] * 1000
        return pulse

    @micropython.native
    def set_offset(self, offset:float):
        """
        TODO
        """
        self.offset = offset
        self.gain = self.offset / self.output_voltage_at_minimal_gain
        voltage_resolution = 4096
        self.points_per_volt = int(self.calibration_factor * voltage_resolution / self.gain)

    @micropython.native
    def get_value(self, voltage:float):
        v = voltage - self.offset
        return int(v * self.points_per_volt)

    @micropython.native
    def pulse_from_voltage(self, voltage:float) -> list[int]:
        value = self.get_value(voltage)
        return [value] * self.max_points

    @micropython.native
    def set_calibration(self, output_voltage_at_minimal_gain:float, calibration_factor:float):
        self.output_voltage_at_minimal_gain = output_voltage_at_minimal_gain
        self.calibration_factor = calibration_factor

    @micropython.native
    def get_frequency(self):
        """
        TODO
        """
        return self.frequency

    @micropython.native
    def get_max_points(self):
        """
        TODO
        """
        return self.max_points

    @micropython.native
    def pulse_from_config(self, ps_config:list[list[float]], padding:bool = False) -> list[int]:
        """
        TODO
        """
        pulse = []
        for point in ps_config:
            t = point[0]
            v = point[1] - self.offset
            n = int(t * self.points_per_ns)
            value = int(v * self.points_per_volt)
            pulse += [value] * n
        # padding with last value
        if padding:
            length = len(pulse)
            if length < self.max_points:
                last_value = pulse[-1]
                pulse += [last_value] * (self.max_points - length)
        # sanity check
        if len(pulse) > self.max_points:
            raise Exception("Erroneous pulse config: pulse too large.")
        return pulse

    @micropython.native
    def pulse_from_spline(self, xpoints:list[int], ypoints:list[float], padding:bool = False) -> list[int]:
        """
        TODO
        """
        if len(xpoints) != len(ypoints):
            raise Exception("xpoints and ypoints have different lengths.")
        if len(xpoints) == 0:
            raise Exception("No spline points provided.")
        tpoints = [0] * len(xpoints)
        vpoints = [0] * len(xpoints)
        for i in range(len(xpoints)):
            tpoints[i] = int(xpoints[i] * self.points_per_ns)
            vpoints[i] = int((ypoints[i] - self.offset) * self.points_per_volt)
        for i in range(1, len(tpoints)):
            if tpoints[i] <= tpoints[i - 1]:
                raise Exception("xpoints must be strictly increasing.")
        if tpoints[-1] >= self.max_points:
            raise Exception("Erroneous pulse config: pulse too large.")
        a = tpoints[0]
        b = tpoints[-1]
        if a == b:
            self.pulse = [vpoints[0]]
            return self.pulse
        pulse_length = b - a + 1
        if pulse_length > self.max_points:
            raise Exception("Erroneous pulse config: pulse too large.")
        if len(tpoints) == 2:
            self.pulse = [0] * pulse_length
            start_value = vpoints[0]
            delta_value = vpoints[1] - start_value
            for i in range(pulse_length):
                self.pulse[i] = start_value + int((delta_value * i) / (pulse_length - 1))
            return self.pulse

        # Stream the PCHIP interpolation directly into the output buffer so long
        # pulses do not need additional full-size temporary lists.
        if len(self.pulse) != pulse_length:
            self.pulse = [0] * pulse_length

        n = len(tpoints)
        h = [0] * (n - 1)
        delta = [0] * (n - 1)
        for i in range(n - 1):
            h[i] = tpoints[i + 1] - tpoints[i]
            delta[i] = (vpoints[i + 1] - vpoints[i]) / h[i]

        m = [0] * n
        m[0] = delta[0]
        m[-1] = delta[-1]
        for i in range(1, n - 1):
            if delta[i - 1] * delta[i] > 0:
                m[i] = 2 / (1 / delta[i - 1] + 1 / delta[i])
            else:
                m[i] = 0

        segment = 0
        for index in range(pulse_length):
            x_val = a + index
            while segment < (n - 2) and x_val > tpoints[segment + 1]:
                segment += 1
            h_i = h[segment]
            t = (x_val - tpoints[segment]) / h_i
            t2 = t * t
            t3 = t2 * t
            h00 = (1 + 2 * t) * (1 - t) * (1 - t)
            h10 = t * (1 - t) * (1 - t)
            h01 = t2 * (3 - 2 * t)
            h11 = t3 - t2
            self.pulse[index] = int(
                h00 * vpoints[segment]
                + h10 * h_i * m[segment]
                + h01 * vpoints[segment + 1]
                + h11 * h_i * m[segment + 1]
            )
        if len(self.pulse) > self.max_points:
            raise Exception("Erroneous pulse config: pulse too large.")
        return self.pulse

    @micropython.native
    def pulse_from_lambda(self, ps_lambda, total_pulse_duration:int, padding:bool = False) -> list[int]:
        """
        TODO
        """
        if self.total_pulse_duration != total_pulse_duration:
            pulse_number_of_points = self.calculate_pulse_number_of_points(total_pulse_duration)
            self.pulse = [0] * pulse_number_of_points
            self.total_pulse_duration = total_pulse_duration
        else:
            pulse_number_of_points = len(self.pulse)
        t = 0
        dt = self.time_resolution
        for i in range(pulse_number_of_points):
            self.pulse[i] = int((ps_lambda(t) - self.offset) * self.points_per_volt)
            t += dt
        # padding with last value
        if padding:
            if pulse_number_of_points < self.max_points:
                last_value = self.pulse[-1]
                self.pulse += [last_value] * (self.max_points - pulse_number_of_points)
        return self.pulse

    @micropython.native
    def pulse_from_list(self, pulse:list[int], padding:bool = False) -> list[int]:
        """
        Puls is generated from raw list without offset or gain correction applied.
        """
        # padding with last value
        if padding:
            length = len(pulse)
            if length < self.max_points:
                last_value = pulse[-1]
                pulse += [last_value] * (self.max_points - length)
        # sanity check
        if len(pulse) > self.max_points:
            raise Exception("Fatal error: pulse too large.")
        return pulse
