Mesh.CharacteristicLengthFactor = 0.1415 / 0.5;

lboxin = 1; lboxout = 1.1;

radius = 0.05; xc = -0.25; yc = -0.25; zc = 0.0;


SetFactory("OpenCASCADE");

Box(1) = {-lboxin/2, -lboxin/2, -lboxin/2, lboxin, lboxin, lboxin};
Box(2) = {-lboxout/2, -lboxout/2, -lboxout/2, lboxout, lboxout, lboxout};
Sphere(3) = {xc, yc, zc, radius, -Pi/2, Pi/2, 2*Pi};
Box(4) = {0.0, 0.0, -0.15, 0.3, 0.3, 0.3};
Box(5) = {0.0, -0.4, -0.15, 0.3, 0.3, 0.3};

Coherence;


air = 1; disk = 2; box = 3; pml = 4; skin = 5;

Physical Volume(air) = {6};
Physical Volume(disk) = {3};
Physical Volume(box) = {4,5};
Physical Volume(pml) = {7};
Physical Surface(skin) = {32,33,34,35,36,37};
