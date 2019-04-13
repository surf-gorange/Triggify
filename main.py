import sys
import re
from itertools import chain
from time import sleep


# This function converts string ints into ints, and string floats into floats (.vmf's use both ints and floats for coordinates)
def num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)


class Vertex:
    height = 2  # Trigger_teleport's size on the Z axis

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

        self.fz = z  # fz represents the fixed z coordinate that gets exported (in generated_triggers.vmf)

    def compare(self, other):
        #print(self.x, self.y, other.x, other.y)

        # This script works by taking a shape and moving the vertices on the top face up 2 units, and the vertices on the bottom
        # face are moved up to where the top face vertices were.
        # To figure out when to add 2 to the height (z) or when to move it up to the top face vertex, we compare 2 vertices' x and y
        # coordinates, if they're equal we can then compare their z coordinate, if it's bigger we add 2, if it's lower we
        # give it the other vertex's z coordinate. If they're equal we can just ignore it (some vertices are shared by several faces)
        # All the z coordinate manipulation is done to fz, which is only used at the end when exported to a file.
        if self.x == other.x and self.y == other.y:
            if self.z < other.z:
                self.fz = other.z
                #print("HERE:", self.fz, self.z, other.z)
                return True

            elif self.z > other.z:
                self.fz += self.height
                return True

    # This is used when generating "generated_triggers.vmf"
    def return_fixed_z(self):
        return self.x, self.y, self.fz


class Face:
    id_counter = 1  # vmf's use id's for faces, no idea how they work, this might not even be necessary.

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
    id_counter = 1  # Same comment as for face's id_counter
    teleport_target = "default"
    use_landmark_angles = True
    csgo = 0  # 0 is csgo, 1 is css

    def __init__(self, *args: Face):
        self.faces = []  # Shapes are not limited to 6 faces, they can be more or less
        self.faces.extend(args)

    def get_all_vertices(self):
        # This returns every single vertex on this shape (a normal cube has (number of faces * 3 = 6 * 3 = 18) vertices)
        return list(chain.from_iterable([f.return_all() for f in self.faces]))

    def check(self):
        all_vertices = self.get_all_vertices()

        # Here we compare every single vertex on a shape against all other vertices, some vertices are repeated but it doesn't
        # matter because it's really fast anyways (see Vertex.compare function for more information)
        for v in all_vertices:
            for v2 in all_vertices:
                if v.compare(v2):
                    # If the compare function fixes the z coordinate, we don't need to keep comparing so we skip to next vertex
                    break

            # If the vertex didn't find any matches (aka rotated solids, etc...) we just add 2 to the z axis and the
            # user has to manually fix it (if they want to, it's still usable just not as pretty)
            # If all vertices of a solid are on unique x and y coordinates, the entire shape is essentially just moved
            # up 2 units
            if v.z == v.fz:
                v.fz += 2

    # This bad boy mimics how vmf's work, it's ugly as sin, but what can you do without an API?
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

# Pretty ugly try/except block here, but in case of a big crash it could help me find a solution
try:
    indent = 20  # Indent represents the current level of indentation in the .vmf at that current line
    found = False  # If it found a face with the texture we're looking for
    Shape.csgo = int(input("CS:GO or CS:S (0 or 1): "))
    Vertex.height = int(input("Trigger height (2 is recommended): "))
    match = input("Texture name (ex: ADS/AD01): ").upper()  # In vmf's all texture names are capitalized, don't know why
    Shape.teleport_target = input("Remote destination: ")
    Shape.use_landmark_angles = int(input("Use landmark angles (0 or 1): "))
    shape_list = []
    face_list = []

    # Here we open the file that was dragged onto the script/executable
    with open(sys.argv[1], "r") as vmf:
        # We painstakingly go through every single line of the .vmf
        for line in vmf.readlines():
            if "solid" in line:
                # This indent variable keeps track of opening and closing curly braces, once this gets back to 0
                # we know we've read the entire solid
                indent = 0
                continue

            if '"plane"' in line:
                # Every face has 3 vertices, these are extracted below
                vert_list = []
                # This isn't very pretty but it gets the job of turning a string into usable data done
                l = re.findall(r'\(.*?\)', line)
                for vert in l:
                    str_vert = vert[1:-1]
                    vert_list.append(Vertex(*[num(n) for n in str_vert.split(" ")]))

                face_list.append(Face(*vert_list))

            # If we find the texture we're looking for
            if match in line:
                found = True

            if "{" in line:
                indent += 1

            if "}" in line:
                indent -= 1

            # Once everything in the solid has been read
            if not indent:
                # Once a solid shows up in the .vmf we keep track of every face of that solid, if we find the texture,
                # we store every face previously extracted, otherwise we just reset and start all over again
                if found:
                    shape_list.append(Shape(*face_list))
                    face_list = []
                    found = False
                    # When reading a solid, indent usually fluctuates by 3, here we're just making sure it's not going
                    # to accidentally trigger "if not indent" a couple lines above
                    indent = 20
                face_list = []

    # Here's where it calls the function to calculate all the fixed z coordinates
    for shape in shape_list:
        shape.check()

    # This beauty is all the other stuff that goes into a fresh .vmf, we add all the generated trigger_teleports at the end
    # of this string
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
            # Here we generate the text that .vmf files can read
            gen.writelines(shape.generate_shape())

    print("-------------------")
    print("Done")

    sleep(2)

# Pretty bad error logging system, but whatever
except Exception as e:
    with open("crashlog.txt", "a+") as log:
        log.write(str(e) + "\n" + "-----------------------")



    print("ERROR: See crash log")
    sleep(2)
