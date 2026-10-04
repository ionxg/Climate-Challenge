// EggCycle: parametric model of the egg digester (all sizes in mm at full scale).
// Open in OpenSCAD (openscad.org), press F6 to render, then File > Export > STL.
// `model_scale = 0.1` gives a 1:10 desk model (~15 cm tall) for the pitch table.
// Same shape as figures/eggcycle-3d.html.

model_scale = 0.1;
part = "all";  // "all", "egg" or "base": print egg and base separately to avoid supports

egg_r = 300;       // max radius
egg_h = 900;       // height
egg_taper = 0.12;  // >0 makes the bottom wider than the top
base_r = 410;
base_h = 500;
gap = 60;          // egg bottom sits this far above the base (cradle + tap pipe)
$fn = 96;

egg_zc = base_h + gap + egg_h / 2;  // egg centre height

function egg_rad(t) = egg_r * sqrt(max(0, 1 - t * t)) * (1 - egg_taper * t);
function egg_z(t) = egg_zc + egg_h / 2 * t;
egg_profile = [for (i = [0:80]) let(t = -1 + 2 * i / 80) [egg_rad(t), egg_h / 2 * t]];

module pipe(from, to, r = 12) {
  hull() { translate(from) sphere(r); translate(to) sphere(r); }
}

module egg() {
  translate([0, 0, egg_zc]) rotate_extrude() polygon(egg_profile);
  // status band
  translate([0, 0, egg_zc]) rotate_extrude() translate([egg_r, 0]) circle(8);

  // food inlet chute + hopper, tilted 45° out of the front (+y)
  t_in = 0.45;
  translate([0, egg_rad(t_in) - 20, egg_z(t_in)]) rotate([-45, 0, 0]) {
    cylinder(r = 60, h = 160);
    translate([0, 0, 155]) cylinder(r1 = 65, r2 = 130, h = 110);
    translate([0, -30, 270]) rotate([20, 0, 0]) cylinder(r = 135, h = 15);  // lid
  }

  // gas valve, relief valve, H2S filter and pipe down the back (-y)
  translate([0, 0, egg_z(1) - 10]) cylinder(r1 = 40, r2 = 30, h = 50);
  translate([50, 0, egg_z(1) - 30]) cylinder(r = 14, h = 60);
  translate([50, 0, egg_z(1) + 30]) cylinder(r = 22, h = 20);
  pipe([0, -20, egg_z(1) + 40], [0, -120, egg_z(1) + 60]);
  pipe([0, -120, egg_z(1) + 60], [0, -330, egg_z(0.4)]);
  pipe([0, -330, egg_z(0.4)], [0, -360, egg_z(-0.2)]);
  pipe([0, -360, egg_z(-0.2)], [0, -360, base_h + 290]);
  translate([0, -360, base_h]) cylinder(r = 50, h = 280);

  // digestate tap out of the bottom, over the base to the front
  pipe([0, 0, egg_z(-1)], [0, 60, egg_z(-1) - 25], 18);
  pipe([0, 60, egg_z(-1) - 25], [0, 450, base_h + 35], 18);
  translate([0, 460, base_h + 10]) cylinder(r = 16, h = 60);

  // cradle: ring + 3 legs
  t_ring = -0.8;
  translate([0, 0, egg_z(t_ring)]) rotate_extrude() translate([egg_rad(t_ring) + 10, 0]) circle(18);
  for (a = [90, 210, 330])
    pipe([cos(a) * (egg_rad(t_ring) + 10), sin(a) * (egg_rad(t_ring) + 10), egg_z(t_ring)],
         [cos(a) * (egg_rad(t_ring) + 60), sin(a) * (egg_rad(t_ring) + 60), base_h], 14);
}

module base() {
  // pod holding the 150 L gas bag, battery and inverter
  cylinder(r1 = base_r + 10, r2 = base_r, h = base_h);
  // plug panel + display on the front
  translate([-170, base_r - 45, 185]) cube([340, 60, 170]);
  translate([-100, base_r - 40, 380]) cube([200, 50, 60]);
  // ESP32 hub on the side
  translate([base_r - 20, 5, 300]) cube([60, 90, 120]);
  // generator module behind, with exhaust
  translate([-230, -base_r - 370, 0]) cube([460, 340, 400]);
  translate([170, -700, 0]) cylinder(r = 25, h = 750);
}

scale(model_scale) {
  if (part == "all" || part == "egg") egg();
  if (part == "all" || part == "base") base();
}
