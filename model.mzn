bool: do_schedule_rooms;
bool: optimize_distances;
bool: use_alternating_weeks;

int: num_days;
int: num_periods;
int: num_subjects;
int: num_teachers;
int: num_rooms;
int: num_classes;
int: num_courses;
set of int: Days = 0..num_days-1;
set of int: Periods = 0..num_periods-1;
set of int: Subjects = 0..num_subjects-1;
set of int: Teachers = 0..num_teachers-1;
set of int: Rooms = 0..num_rooms-1;
set of int: Classes = 0..num_classes-1;
set of int: Courses = 0..num_courses-1;

array[Rooms, Rooms] of int: room_distances;

% SubjectData
array[Subjects] of set of Classes: subjects__classes;
array[Subjects] of int: subjects__periods_per_week;
array[Subjects] of set of Teachers: subjects__teachers;
array[Subjects] of int: subjects__teachers_per_period;
array[Subjects] of set of Rooms: subjects__rooms;
array[Subjects] of int: subjects__rooms_per_period;
array[Subjects, Days, Periods] of bool: subjects__available_periods;

% TeacherData
array[Teachers, Days, Periods] of bool: teachers__available_periods;

% RoomData
array[Rooms, Days, Periods] of bool: rooms__available_periods;

% CourseData
array[Courses] of bool: courses__equal_teacher_distribution;
array[Courses] of bool: courses__manual_teacher_distribution;
array[Courses] of set of Teachers: courses__teachers;
array[Courses] of int: courses__teachers_per_period;
array[Courses, Teachers] of int: courses__distribution;
array[Courses] of set of Subjects: courses__subjects;

array[Days, Periods, Subjects] of var 0..1: schedule_subjects;

% Each subject should appear exactly 'n' times during the week
constraint forall(s in Subjects)(
    sum(d in Days, p in Periods)(schedule_subjects[d, p, s]) = subjects__periods_per_week[s]
);

% Ensure subjects from the same class do not overlap in the same period
constraint forall(c in Classes, d in Days, p in Periods)(
    sum(s in Subjects where c in subjects__classes[s])(schedule_subjects[d, p, s]) <= 1
);

% Avoid duplicate subject in each day (subject s should appear at most once per day)
constraint forall(d in Days, s in Subjects)(
    sum(p in Periods)(schedule_subjects[d, p, s]) <= 1
);

% Ensure subjects arent't schedule where they are not available
constraint forall(d in Days, p in Periods, s in Subjects where (not subjects__available_periods[s, d, p]))(
    schedule_subjects[d, p, s] = 0
);

%* Teacher constraints

% Assign teachers to subjects
array[Subjects, Teachers] of var 0..1: teacher_assignments;
constraint forall(s in Subjects)(
    % Ensure that the number of teachers assigned matches subjects__teachers_per_period[s]
    sum(t in Teachers)(teacher_assignments[s, t]) = subjects__teachers_per_period[s]
);

% Ensure that the teachers assigned to each subject are valid (i.e., from the allowed set of teachers for that subject)
constraint forall(s in Subjects, t in Teachers)(
    % equivalent to: 
    % t not in subject__teachers[s] -> teacher_assignment[s, t] = 0
    % teacher_assignment[s, t] = 1 -> in subject__teachers[s]
    t in subjects__teachers[s] \/ teacher_assignments[s, t] = 0
);

% Ensure that if two subjects share the same teacher, they cannot be scheduled in the same period
constraint forall(d in Days, p in Periods, t in Teachers)(
    sum(s in Subjects)(teacher_assignments[s, t] * schedule_subjects[d, p, s]) <= 1
);

% Ensure teachers arent't schedule where they are not available
constraint forall(d in Days, p in Periods, s in Subjects, t in Teachers where (not teachers__available_periods[t, d, p]))(
    teacher_assignments[s, t] * schedule_subjects[d, p, s] = 0
);

constraint forall(
    q in Courses where courses__equal_teacher_distribution[q],
    t in courses__teachers[q]
)(
    let {
        int: periods_per_teacher = (courses__teachers_per_period[q] * card(courses__subjects[q])) div card(courses__teachers[q]),
        bool: divisible = (courses__teachers_per_period[q] * card(courses__subjects[q]) mod card(courses__teachers[q])) = 0
    } in
    if divisible then
        sum(s in courses__subjects[q])(teacher_assignments[s, t]) = periods_per_teacher
    else
        sum(s in courses__subjects[q])(teacher_assignments[s, t]) = periods_per_teacher \/
        sum(s in courses__subjects[q])(teacher_assignments[s, t]) = periods_per_teacher + 1
    endif
);

constraint forall(
    q in Courses where courses__manual_teacher_distribution[q],
    t in Teachers)(
        courses__distribution[q, t] == 0 \/ sum(s in courses__subjects[q])(teacher_assignments[s, t]) = courses__distribution[q, t]
);

%* Room constraints
% Similar structure to teacher constraints

% Assign rooms to subjects
array[Subjects, Rooms] of var 0..1: room_assignments;
constraint do_schedule_rooms -> forall(s in Subjects)(
    % Ensure that the number of rooms assigned matches subjects__rooms_per_period[s]
    sum(r in Rooms)(room_assignments[s, r]) = subjects__rooms_per_period[s]
);

% Ensure that the rooms assigned to each subject are valid (i.e., from the allowed set of rooms for that subject)
constraint do_schedule_rooms -> forall(s in Subjects, r in Rooms)(
    % equivalent to: 
    % r not in subject__rooms[s] -> room_assignment[s, r] = 0
    % room_assignment[s, r] = 1 -> in subject__rooms[s]
    r in subjects__rooms[s] \/ room_assignments[s, r] = 0
);

% Ensure that if two subjects share the same room, they cannot be scheduled in the same period
constraint do_schedule_rooms -> forall(d in Days, p in Periods, r in Rooms)(
    sum(s in Subjects)(room_assignments[s, r] * schedule_subjects[d, p, s]) <= 1
);

% Ensure rooms arent't schedule where they are not available
constraint forall(d in Days, p in Periods, s in Subjects, r in Rooms where (not rooms__available_periods[r, d, p]))(
    room_assignments[s, r] * schedule_subjects[d, p, s] = 0
);

% Alternating week constraints
set of int: HalfDays = 0..(num_days div 2 - 1);
constraint use_alternating_weeks -> forall(s in Subjects)(
    if subjects__periods_per_week[s] mod 2 = 0 then
        forall(d in HalfDays, p in Periods)(
            schedule_subjects[d, p, s] = schedule_subjects[d + num_days div 2, p, s]
        )
    else
        sum(d in HalfDays, p in Periods)(
            schedule_subjects[d, p, s] * schedule_subjects[d + num_days div 2, p, s]
        ) = subjects__periods_per_week[s] div 2
    endif
);

%* Room distances constraints

array[Classes, Days, Periods] of var opt Rooms: schedule_rooms_by_class = 
    array3d(Classes, Days, Periods, [
        if not optimize_distances then
            0
        else
            if sum(
                s in Subjects where c in subjects__classes[s]
                /\ subjects__rooms_per_period[s] == 1, 
                r in subjects__rooms[s]
            )(
                room_assignments[s, r] * schedule_subjects[d, p, s]
            ) = 0
            then
                <>
            else
                sum(
                    s in Subjects where c in subjects__classes[s]
                    /\ subjects__rooms_per_period[s] == 1, 
                    r in subjects__rooms[s]
                )(
                    room_assignments[s, r] * schedule_subjects[d, p, s] * r
                )
            endif
        endif
        |
        c in Classes,
        d in Days,
        p in Periods
    ]);


array[Classes, Days, 0..num_periods-2] of var opt int: distances;
constraint optimize_distances -> distances = array3d(Classes, Days, 0..num_periods-2, [
    let {
        var opt int: r1 = schedule_rooms_by_class[c, d, p],
        var opt int: r2 = schedule_rooms_by_class[c, d, p + 1]
    } in 
    room_distances[r1, r2]
    |
    c in Classes,
    d in Days,
    p in 0..num_periods-2
]);


var int: sum_distances;
constraint optimize_distances -> sum_distances = sum(c in Classes, d in Days, p in 0..num_periods-2)(distances[c, d, p]);

var int: max_distance;
constraint optimize_distances -> max_distance = max(c in Classes, d in Days)(sum(p in 0..num_periods-2)(distances[c, d, p]));

solve minimize max_distance;
% solve satisfy;
output "\(sum_distances) \(max_distance)";
% output "";
