# Schedule Input Structure

## Root

```
config: Config
days: int
periods: int
teachers: TeacherData[]
classes: ClassData[]
rooms: RoomData[]                  if config.schedule_room
room_distances: RoomIndex[][]      if config.optimize_distances
subjects: Subject[]
```

## Config

```
optimize_distance: bool
use_alternating_weeks: bool
schedule_rooms: bool
```

## TeacherData

```
name: str
available_periods?: Period[]
```

## ClassData

```
name: str
```

## RoomData

```
name: str
```

## Subject

```
classes: ClassIndex[]
periods_per_week: int
teachers: TeacherIndex[]
teachers_per_period: int
available_rooms: RoomIndex[]       if config.schedule_room
rooms_per_period: int              if config.schedule_room
name: str
available_periods?: Period[]
```

## Period

`[int, int]`

## ClassIndex

`int`

## TeacherIndex

`int`

## RoomIndex

`int`