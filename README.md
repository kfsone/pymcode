Python MCode generator

Helper functions for generating Marlin mcodes/gcodes from human-friendly names,
along with helpers to "execute" that by turning it into a contiguous script.

Supports line number tracking, checksumming and optional comments.


```python
import codes
import run

start_seq = [
	codes.home_axis(),		# home all axes
	codes.set_units('mm'),
]
gcode_seq = [
	# ... sliced gcodes
]
end_seq = [
	codes.zero_extruded_length(),
	codes.set_positioning("relative"),
	codes.move(z=10),		# move up a little
	codes.set_positioning("absolute"),
	# Finally move x and y home - leaving the head above the last print
	codes.home_axis(x=True, y=True)
]

script = codes.Run()
script.queue(start_seq)
script.execute(gcode_seq) # execute queued commands first then gcode_seq

script.queue(codes.set_hotendtemp(0))
script.execute(codes.set_bedtemp(0))  # executes set_hotendtemp first

# Turn the fan off.
script.execute_immediate(codes.set_fanoff())	# would skip any queue
```

