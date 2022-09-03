class Priorities:
    def __init__(self, person_id, priority=1):
        self.person_id = person_id
        self.priority = priority


artem = Priorities(1221)
print(type(artem.priority))

