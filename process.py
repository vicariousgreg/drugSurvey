ignore_once = True
ignore_month = False
restrict_alcohol = False
restrict_caffeine = False
restrict_nicotine = False
restrict_cannabis = False

substances = []
if not restrict_alcohol:
    substances.append("Alcohol")
if not restrict_caffeine:
    substances.append("Caffeine")
if not restrict_nicotine:
    substances.append("Nicotine")
if not restrict_cannabis:
    substances.append("Cannabis")

substances.append("Barbiturates")
substances.append("Benzodiazepines")
substances.append("Other Hypnotics")
substances.append("Opiods")
substances.append("Inhalants")
substances.append("MDMA")
substances.append("Methamphetamine")
substances.append("Pharmaceutical Amphetamines")
substances.append("Ritalin")
substances.append("Cocaine")
substances.append("Crack Cocaine")
substances.append("Psychedelic Hallucinogens")
substances.append("Dissociative Hallucinogens")
substances.append("Deliriant Hallucinogens")
substances.append("Steroids")
substances.append("Antidepressants")
substances.append("Other")

groups = dict([
    ("Depressants", 
        [
            "Barbiturates",
            "Benzodiazepines",
            "Other Hypnotics",
            "Opiods",
            "Inhalants"
        ]
    ),
    ("Stimulants",
        [
            "MDMA",
            "Methamphetamine",
            "Pharmaceutical Amphetamines",
            "Ritalin",
            "Cocaine",
            "Crack Cocaine",
        ]
    ),
    ("Alcohol",
        [ ]
    ),
    ("Nicotine",
        [ ]
    ),
    ("Caffeine",
        [ ]
    ),
    ("Hallucinogens",
        [
            "Psychedelic Hallucinogens",
            "Dissociative Hallucinogens",
            "Deliriant Hallucinogens",
        ]
    ),
    ("Cannabis",
        [ ]
    ),
    ("Antidepressants",
        ["Antidepressants"]
    ),
    ("Other",
        [
            "Steroids",
            "Other"
        ]
    )
])
if not restrict_alcohol:
    groups["Alcohol"].append("Alcohol")
if not restrict_caffeine:
    groups["Caffeine"].append("Caffeine")
if not restrict_nicotine:
    groups["Nicotine"].append("Nicotine")
if not restrict_cannabis:
    groups["Cannabis"].append("Cannabis")

inverse_groups = dict()
for gr,vals in groups.iteritems():
    for val in vals:
        inverse_groups[val] = gr

substance_goods = []
for substance in substances:
    if not ignore_once: substance_goods.append("Once " + substance)
    if not ignore_month: substance_goods.append("Month " + substance)
    substance_goods.append("Daily " + substance)

group_goods = []
for group in groups:
    if not ignore_once: group_goods.append("Once " + group)
    if not ignore_month: group_goods.append("Month " + group)
    group_goods.append("Daily " + group)

def generate_goods():
    with open("data/substance_goods.txt", "w+") as f:
        for good in substance_goods: f.write(good + "\n")
    with open("data/group_goods.txt", "w+") as f:
        for good in group_goods: f.write(good + "\n")
    with open("data/c_substance_goods.txt", "w+") as f:
        for substance in substances: f.write(substance + "\n")
    with open("data/c_group_goods.txt", "w+") as f:
        for good in groups: f.write(good + "\n")

class Entry:
    def __init__(self, responses):
        self.responses = responses
        self.usage = dict()
        self.group_usage = dict()
        self.once = set()
        self.month = set()
        self.daily = set()
        self.substances_bag = set()
        self.group_bag = set()
        for line in self.responses[1]:
            if restrict_alcohol and "Alcohol" in line:
                continue
            if "Used at Least Once" in line:
                if ignore_once: continue
                substance = line[:line.index("Used")].strip()
                substance = substance.split("(")[0].strip()
                self.usage[substance] = 0

                try:
                    group = inverse_groups[substance]
                    if group not in self.group_usage:
                        self.group_usage[group] = 0
                except KeyError: pass

                self.once.add(substance)
                self.substances_bag.add("Once " + substance)
                try: self.group_bag.add("Once " + inverse_groups[substance])
                except KeyError: pass
            elif "Used in Past 30 Days" in line:
                if ignore_month: continue
                substance = line[:line.index("Used")].strip()
                substance = substance.split("(")[0].strip()
                self.usage[substance] = 1

                try:
                    group = inverse_groups[substance]
                    if group not in self.group_usage or \
                           self.group_usage[group] < 1:
                        self.group_usage[group] = 1
                except KeyError: pass

                self.month.add(substance)
                self.substances_bag.add("Month " + substance)
                try: self.group_bag.add("Month " + inverse_groups[substance])
                except KeyError: pass
            elif "Used Daily for Past 30 Days" in line:
                substance = line[:line.index("Used")].strip()
                substance = substance.split("(")[0].strip()
                self.usage[substance] = 2

                try:
                    group = inverse_groups[substance]
                    if group not in self.group_usage or \
                           self.group_usage[group] < 1:
                        self.group_usage[group] = 2
                except KeyError: pass

                self.daily.add(substance)
                self.substances_bag.add("Daily " + substance)
                try: self.group_bag.add("Daily " + inverse_groups[substance])
                except KeyError: pass

        # Remove smaller group values
        # ie Once stimulant, Daily stimulant
        values = ["Once", "Month", "Daily"]
        for group in groups:
            max_value = -1
            for item in self.group_bag:
                value,gr = tuple(item.split())
                if gr == group and values.index(value) > max_value:
                    max_value = values.index(value)
            if max_value > -1:
                for key in values:
                    try: self.group_bag.remove(key + " " + group)
                    except KeyError: pass
                self.group_bag.add(values[max_value] + " " + group)

        for i in xrange(2, 9):
            self.responses[i] = " ".join(self.responses[i])
            null_responses = ["Respondent skipped this question",
                "N/A", "N/a", "M/A", "No", "None", "no", "No.", "nah",
                "No I have not.", "I have not.", "No, I have not."]
            if self.responses[i] in null_responses:
                del self.responses[i]

    def get_substances_line(self):
        data = []
        for item in self.substances_bag:
            try: data.append(str(substance_goods.index(item)))
            except ValueError: pass
        return ",".join(data)

    def get_groups_line(self):
        data = []
        for item in self.group_bag:
            try: data.append(str(group_goods.index(item)))
            except ValueError: pass
        return ",".join(data)

    def print_entry(self):
        if len(self.once) > 0:
            print("Used at Least Once:")
            for substance in self.once: print("  " + substance)
        if len(self.month) > 0:
            print("Used in Past 30 Days:")
            for substance in self.month: print("  " + substance)
        if len(self.daily) > 0:
            print("Used Daily for Past 30 Days:")
            for substance in self.daily: print("  " + substance)
        print("")



def read_data():
# Read data and create entries
    entries = []
    response = None
    count = 0
    in_response = False
    current_q = 1

    output = []

    for f in ("data/survey1.txt", "data/survey2.txt"):
        lines = list(l.strip() for l in open(f).readlines())
        for line in lines:
            if "Q1:" in line:
                if response:
                    entries.append(Entry(response))
                in_response=True
                response = dict()
                output.append("Response %d" % (count))
            elif "Edit Delete Export" in line:
                output.append("")
                in_response = False
                count += 1

            if in_response:
                output.append(line)
                if line.startswith("Q"):
                    current_q = int(line[1])
                    response[current_q] = []
                else:
                    response[current_q].append(line)
        if response:
            entries.append(Entry(response))
        in_response=True
        response = dict()
        output.append("Response %d" % (count))

    with open("data/clean_survey.txt", "w+") as f:
        for line in output: f.write(line + "\n")

    return entries

def generate_items(entries):
    with open("data/substance_items.csv", "w+") as f:
        for i,entry in enumerate(entries):
            line = entry.get_substances_line()
            if len(line) > 0:
                f.write("%d,%s\n" % (i,line))

    with open("data/group_items.csv", "w+") as f:
        for i,entry in enumerate(entries):
            line = entry.get_groups_line()
            if len(line) > 0:
                f.write("%d,%s\n" % (i,line))

    with open("data/substance_clustering.csv", "w+") as f:
        for entry in entries:
            line = entry.get_substances_line()
            data = []
            for sub in substances:
                #data.append(str((entry.usage.get(sub, -1)+1)**2))
                data.append(str((entry.usage.get(sub, -1)+1)))
            if all(x == "0" for x in data): continue
            line = ",".join(data)
            if len(line) > 0:
                f.write("%s\n" % line)

    with open("data/group_clustering.csv", "w+") as f:
        for entry in entries:
            line = entry.get_groups_line()
            data = []
            for group in groups:
                #data.append(str((entry.group_usage.get(group, -1)+1)**2))
                data.append(str((entry.group_usage.get(group, -1)+1)))
            if all(x == "0" for x in data): continue
            line = ",".join(data)
            if len(line) > 0:
                f.write("%s\n" % line)

def print_table(entries):
# Print table
    symbols = ["-", "+", "#"]
    ordered_substances = sorted(substances, reverse=True,
        key = lambda sub: len([entry for entry in entries if any(sub in y for y in entry.substances_bag)]))
    for i in xrange(max(len(s) for s in ordered_substances)):
        chars = []
        for s in ordered_substances:
            if len(s) > i: chars.append(s[i])
            else: chars.append(" ")
        print("   ".join(chars))

    for entry in entries:
        line = []
        for substance in ordered_substances:
            try:
                line.append(symbols[entry.usage[substance]])
            except:
                line.append(" ")
        print("   ".join(line))

generate_goods()
entries = read_data()
generate_items(entries)
print_table(entries)
