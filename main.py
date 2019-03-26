import sys
import re
from itertools import chain
from time import sleep


def num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)


class Vertex:
    height = 2

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

        self.fz = z

    def compare(self, other):
        #print(self.x, self.y, other.x, other.y)
        if self.x == other.x and self.y == other.y:
            if self.z < other.z:
                self.fz = other.z
                #print("HERE:", self.fz, self.z, other.z)
                return True

            elif self.z > other.z:
                self.fz += self.height
                return True

    def return_fixed_z(self):
        return self.x, self.y, self.fz


class Face:
    id_counter = 1
    def __init__(self, v1: Vertex, v2: Vertex, v3: Vertex):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3

    def return_all(self):
        return self.v1, self.v2, self.v3

    def generate_face(self):
        print(*self.v1.return_fixed_z())
        Face.id_counter += 1
        return '''
        side
        {{
            "id" "{9}"
            "plane" "({0} {1} {2}) ({3} {4} {5}) ({6} {7} {8})"
            "material" "TOOLS/TOOLSTRIGGER"
            "uaxis" "[1 0 0 0] 0.5"
            "vaxis" "[0 -1 0 0] 0.5"
            "rotation" "0"
            "lightmapscale" "128"
            "smoothing_groups" "0"
        }}'''.format(*self.v1.return_fixed_z(), *self.v2.return_fixed_z(), *self.v3.return_fixed_z(), self.id_counter)



class Shape:
    id_counter = 1
    teleport_target = "default"
    use_landmark_angles = True
    csgo = 0
    def __init__(self, *args: Face):
        self.faces = []
        self.faces.extend(args)

    def get_all_vertices(self):
        return list(chain.from_iterable([f.return_all() for f in self.faces]))

    def check(self):
        all_vertices = self.get_all_vertices()

        for v in all_vertices:
            for v2 in all_vertices:
                if v.compare(v2):
                    break

            if v.z == v.fz:
                v.fz += 2

    def generate_shape(self):
        s = '''
entity
{{
    "id" "{0}"
    "classname" "trigger_teleport"'''.format(self.id_counter)
        if self.csgo == 0:
            s += '''
    "CheckDestIfClearForPlayer" "0"'''

        s += '''
    "origin" "{0} {1} {2}"
'''.format(*self.faces[0].v1.return_fixed_z())

        if self.csgo == 0:
            s += '    "spawnflags" "4097"'

        elif self.use_landmark_angles:
            s += '    "spawnflags" "33"'

        else:
            s += '    "spawnflags" "1"'

        s += '''
    "StartDisabled" "0"
    "target" "{0}"'''.format(self.teleport_target)

        if self.csgo == 0:
            s += '''
    "UseLandmarkAngles" "{0}"'''.format(int(self.use_landmark_angles))

        s += '''
    solid
    {{
        "id" "{0}"'''.format(self.id_counter)
        Shape.id_counter += 1

        for f in self.faces:
            s += f.generate_face()

        s += '''
        editor
        {
            "color" "0 136 109"
            "visgroupshown" "1"
            "visgroupautoshown" "1"
        }
    }
}'''

        return s

print("Gorange's Triggify v1.1")
print("------------------------------")
print("Put the texture on all the floors you want trigger zones on")
print("Some of the faces on the triggers are buggy you can fix it by", "going into 'Map > Check for problems: 'Fix all (of type)'")
print("Output can be found in 'generated_triggers.vmf'")
print("It sometimes produces invalid shapes, just delete them")
print("Enjoy the time you've saved!")
print("------------------------------")
try:
    print("Selected map: " + str(sys.argv[1]))
except IndexError:
    print("No map selected")
    print("Please drag a .vmf onto this .exe")
    sleep(4)
    quit()
print("------------------------------")

try:
    indent = 20
    found = False
    Shape.csgo = int(input("CS:GO or CS:S (0 or 1): "))
    Vertex.height = int(input("Trigger height (2 is recommended): "))
    match = input("Texture name (ex: ADS/AD01): ").upper()
    Shape.teleport_target = input("Remote destination: ")
    Shape.use_landmark_angles = int(input("Use landmark angles (0 or 1): "))
    shape_list = []
    face_list = []


    with open(sys.argv[1], "r") as vmf:
        for line in vmf.readlines():
            if "solid" in line:
                solid_list = []
                indent = 0
                continue

            if '"plane"' in line:
                vert_list = []
                l = re.findall(r'\(.*?\)', line)
                for vert in l:
                    str_vert = vert[1:-1]
                    vert_list.append(Vertex(*[num(n) for n in str_vert.split(" ")]))

                face_list.append(Face(*vert_list))

            if match in line:
                found = True

            if "{" in line:
                indent += 1

            if "}" in line:
                indent -= 1

            if not indent:
                if found:
                    shape_list.append(Shape(*face_list))
                    face_list = []
                    found = False
                    indent = 20
                face_list = []


    for shape in shape_list:
        shape.check()

    t = '''versioninfo
{
    "editorversion" "400"
    "editorbuild" "8075"
    "mapversion" "0"
    "formatversion" "100"
    "prefab" "0"
}
viewsettings
{
    "bSnapToGrid" "1"
    "bShowGrid" "1"
    "bShowLogicalGrid" "0"
    "nGridSpacing" "64"
    "bShow3DGrid" "0"
}
world
{
    "id" "1"
    "mapversion" "0"
    "classname" "worldspawn"
    "skyname" "sky_dust"
    "maxpropscreenwidth" "-1"
    "detailvbsp" "detail.vbsp"
    "detailmaterial" "detail/detailsprites"
}
cameras
{
    "activecamera" "-1"
}
cordons
{
    "active" "0"
}'''


    with open("generated_triggers.vmf", "w+") as gen:
        gen.writelines(t)
        for shape in shape_list:
            gen.writelines(shape.generate_shape())

    print("-------------------")
    print("Done")

    sleep(2)

except Exception as e:
    with open("crashlog.txt", "a+") as log:
        log.write(str(e) + "\n" + "-----------------------")



    print("ERROR: See crash log")
    sleep(2)
