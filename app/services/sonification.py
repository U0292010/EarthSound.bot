import math
import sys
from array import array
from collections.abc import Sequence

import lameenc


def _encode_mp3(pcm_samples: array, sample_rate: int) -> bytes:
	if sys.byteorder != "little":
		pcm_samples.byteswap()

	encoder = lameenc.Encoder()
	encoder.set_in_sample_rate(sample_rate)
	encoder.set_channels(1)
	encoder.set_bit_rate(128)
	encoder.set_quality(5)
	pcm_data = pcm_samples.tobytes()
	return encoder.encode(pcm_data) + encoder.flush()


def build_temperature_audio(yearly_values: Sequence[tuple[int, float]]) -> bytes:
	if not yearly_values:
		raise ValueError("At least one yearly temperature value is required.")

	sample_rate = 22050
	note_duration = 0.65
	gap_duration = 0.12
	fade_duration = 0.025
	temperatures = [temperature for _, temperature in yearly_values]
	minimum = min(temperatures)
	maximum = max(temperatures)
	pcm_samples = array("h")
	note_sample_count = round(sample_rate * note_duration)
	fade_sample_count = round(sample_rate * fade_duration)
	gap_sample_count = round(sample_rate * gap_duration)

	for temperature in temperatures:
		relative_temperature = (
			(temperature - minimum) / (maximum - minimum)
			if maximum > minimum
			else 0.5
		)
		frequency = 220.0 + relative_temperature * 220.0

		for sample_index in range(note_sample_count):
			fade_in = min(1.0, sample_index / fade_sample_count)
			fade_out = min(1.0, (note_sample_count - sample_index - 1) / fade_sample_count)
			envelope = min(fade_in, fade_out)
			phase = 2 * math.pi * frequency * sample_index / sample_rate
			sample = int(7800 * envelope * (math.sin(phase) + 0.15 * math.sin(phase * 2)))
			pcm_samples.append(sample)

		pcm_samples.extend(array("h", [0]) * gap_sample_count)

	return _encode_mp3(pcm_samples, sample_rate)


def sea_level_beat_durations(yearly_values: Sequence[tuple[int, float]]) -> list[float]:
	if not yearly_values:
		raise ValueError("At least one yearly sea level value is required.")

	levels = [level for _, level in yearly_values]
	minimum = min(levels)
	maximum = max(levels)
	beat_durations = []

	for level in levels:
		relative_level = (level - minimum) / (maximum - minimum) if maximum > minimum else 0.5
		beat_durations.append(0.78 - relative_level * 0.38)

	return beat_durations


def build_sea_level_audio(yearly_values: Sequence[tuple[int, float]]) -> bytes:
	if not yearly_values:
		raise ValueError("At least one yearly sea level value is required.")

	sample_rate = 22050
	fade_duration = 0.02
	fade_sample_count = round(sample_rate * fade_duration)
	pcm_samples = array("h")

	for index, (beat_duration, (_, _)) in enumerate(
		zip(sea_level_beat_durations(yearly_values), yearly_values)
	):
		note_duration = beat_duration * 0.72
		note_sample_count = round(sample_rate * note_duration)
		gap_sample_count = round(sample_rate * (beat_duration - note_duration))
		frequency = 330.0 if index % 2 == 0 else 392.0

		for sample_index in range(note_sample_count):
			fade_in = min(1.0, sample_index / fade_sample_count)
			fade_out = min(1.0, (note_sample_count - sample_index - 1) / fade_sample_count)
			envelope = min(fade_in, fade_out)
			phase = 2 * math.pi * frequency * sample_index / sample_rate
			pcm_samples.append(int(7000 * envelope * math.sin(phase)))

		pcm_samples.extend(array("h", [0]) * gap_sample_count)

	return _encode_mp3(pcm_samples, sample_rate)


def cloud_coverage_note_patterns(
	yearly_values: Sequence[tuple[int, float]],
) -> list[tuple[int, float]]:
	if not yearly_values:
		raise ValueError("At least one yearly cloud coverage value is required.")

	coverage_values = [coverage for _, coverage in yearly_values]
	minimum = min(coverage_values)
	maximum = max(coverage_values)
	patterns = []

	for coverage in coverage_values:
		relative_coverage = (
			(coverage - minimum) / (maximum - minimum)
			if maximum > minimum
			else 0.5
		)
		note_count = 1 + round(relative_coverage * 3)
		note_duration = 0.10 + relative_coverage * 0.16
		patterns.append((note_count, note_duration))

	return patterns


def build_cloud_coverage_audio(yearly_values: Sequence[tuple[int, float]]) -> bytes:
	if not yearly_values:
		raise ValueError("At least one yearly cloud coverage value is required.")

	sample_rate = 22050
	fade_sample_count = round(sample_rate * 0.012)
	pulse_gap_count = round(sample_rate * 0.035)
	year_gap_count = round(sample_rate * 0.10)
	pcm_samples = array("h")
	frequencies = (294.0, 330.0, 392.0, 440.0)

	for year_index, (note_count, note_duration) in enumerate(
		cloud_coverage_note_patterns(yearly_values)
	):
		note_sample_count = round(sample_rate * note_duration)

		for note_index in range(note_count):
			frequency = frequencies[(year_index + note_index) % len(frequencies)]
			for sample_index in range(note_sample_count):
				fade_in = min(1.0, sample_index / fade_sample_count)
				fade_out = min(1.0, (note_sample_count - sample_index - 1) / fade_sample_count)
				envelope = min(fade_in, fade_out)
				phase = 2 * math.pi * frequency * sample_index / sample_rate
				pcm_samples.append(int(6200 * envelope * math.sin(phase)))

			pcm_samples.extend(array("h", [0]) * pulse_gap_count)

		pcm_samples.extend(array("h", [0]) * year_gap_count)

	return _encode_mp3(pcm_samples, sample_rate)


def wildfire_rhythm_patterns(
	yearly_values: Sequence[tuple[int, float]],
) -> list[tuple[float, float]]:
	if not yearly_values:
		raise ValueError("At least one yearly wildfire count is required.")

	counts = [count for _, count in yearly_values]
	minimum = min(counts)
	maximum = max(counts)
	patterns = []

	for count in counts:
		relative_count = (count - minimum) / (maximum - minimum) if maximum > minimum else 0.5
		beat_duration = 0.72 - relative_count * 0.42
		intensity = 0.22 + relative_count * 0.70
		patterns.append((beat_duration, intensity))

	return patterns


def build_wildfire_audio(yearly_values: Sequence[tuple[int, float]]) -> bytes:
	if not yearly_values:
		raise ValueError("At least one yearly wildfire count is required.")

	sample_rate = 22050
	fade_sample_count = round(sample_rate * 0.015)
	pcm_samples = array("h")
	frequencies = (196.0, 220.0, 247.0, 262.0, 294.0)

	for index, ((_, _), (beat_duration, intensity)) in enumerate(
		zip(yearly_values, wildfire_rhythm_patterns(yearly_values))
	):
		note_duration = min(0.18, beat_duration * 0.75)
		note_sample_count = round(sample_rate * note_duration)
		gap_sample_count = round(sample_rate * (beat_duration - note_duration))
		frequency = frequencies[index % len(frequencies)]
		amplitude = int(18000 * intensity)

		for sample_index in range(note_sample_count):
			fade_in = min(1.0, sample_index / fade_sample_count)
			fade_out = min(1.0, (note_sample_count - sample_index - 1) / fade_sample_count)
			envelope = min(fade_in, fade_out)
			phase = 2 * math.pi * frequency * sample_index / sample_rate
			pcm_samples.append(int(amplitude * envelope * math.sin(phase)))

		pcm_samples.extend(array("h", [0]) * gap_sample_count)

	return _encode_mp3(pcm_samples, sample_rate)


def vegetation_instrument(
	vegetation_value: float,
) -> tuple[str, tuple[float, ...], float]:
	if vegetation_value < 25:
		return "Flute", (1.0, 0.10, 0.02), 0.0
	if vegetation_value < 50:
		return "Clarinet", (1.0, 0.0, 0.42, 0.0, 0.12), 0.2
	if vegetation_value < 75:
		return "Marimba", (1.0, 0.55, 0.28, 0.15), 7.0
	return "Strings", (1.0, 0.62, 0.40, 0.28, 0.20), 0.15


def vegetation_instruments(yearly_values: Sequence[tuple[int, float]]) -> list[str]:
	if not yearly_values:
		raise ValueError("At least one yearly vegetation value is required.")

	return [vegetation_instrument(value)[0] for _, value in yearly_values]


def build_vegetation_audio(yearly_values: Sequence[tuple[int, float]]) -> bytes:
	if not yearly_values:
		raise ValueError("At least one yearly vegetation value is required.")

	sample_rate = 22050
	note_duration = 0.52
	gap_sample_count = round(sample_rate * 0.12)
	fade_sample_count = round(sample_rate * 0.02)
	pcm_samples = array("h")
	frequencies = (220.0, 247.0, 262.0, 294.0, 330.0)

	for note_index, (_, vegetation_value) in enumerate(yearly_values):
		_, harmonic_weights, decay_rate = vegetation_instrument(vegetation_value)
		note_sample_count = round(sample_rate * note_duration)
		frequency = frequencies[note_index % len(frequencies)]
		weight_total = sum(harmonic_weights)

		for sample_index in range(note_sample_count):
			fade_in = min(1.0, sample_index / fade_sample_count)
			fade_out = min(1.0, (note_sample_count - sample_index - 1) / fade_sample_count)
			time_seconds = sample_index / sample_rate
			envelope = min(fade_in, fade_out) * math.exp(-decay_rate * time_seconds)
			phase = 2 * math.pi * frequency * time_seconds
			harmonic_wave = sum(
				weight * math.sin(phase * harmonic_index)
				for harmonic_index, weight in enumerate(harmonic_weights, start=1)
			)
			pcm_samples.append(int(9000 * envelope * harmonic_wave / weight_total))

		pcm_samples.extend(array("h", [0]) * gap_sample_count)

	return _encode_mp3(pcm_samples, sample_rate)