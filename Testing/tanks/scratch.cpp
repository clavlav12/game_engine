// step 1
// find the farthest vertex in
// the polygon along the separation normal
int c = vertices.length;
for (int i = 0; i < c; i++) {
  double projection = n.dot(v);
  if (projection > max) {
    max = projection;
    index = i;
  }
}

// step 2
// now we need to use the edge that
// is most perpendicular, either the
// right or the left
Vector2 v = vertices[index];
Vector2 v1 = v.next;
Vector2 v0 = v.prev;
// v1 to v
Vector2 l = v - v1;
// v0 to v
Vector2 r = v - v0;
// normalize
l.normalize();
r.normalize();
// the edge that is most perpendicular
// to n will have a dot product closer to zero
if (r.dot(n) <= l.dot(n)) {
  // the right edge is better
  // make sure to retain the winding direction
      return new Edge(v, v0, v);
} else {
  // the left edge is better
  // make sure to retain the winding direction
  return new Edge(v, v, v1);
}
// we return the maximum projection vertex (v)
// and the edge points making the best edge (v and either v0 or v1)






// clips the line segment points v1, v2
// if they are past o along n
ClippedPoints clip(v1, v2, n, o) {

  ClippedPoints cp = new ClippedPoints();

  double d1 = n.dot(v1) - o;

  double d2 = n.dot(v2) - o;

  // if either point is past o along n

  // then we can keep the point

  if (d1 >= 0.0) cp.add(v1);

  if (d2 >= 0.0) cp.add(v2);

  // finally we need to check if they

  // are on opposing sides so that we can

  // compute the correct point

  if (d1 * d2 < 0.0) {

    // if they are on different sides of the

    // offset, d1 and d2 will be a (+) * (-)

    // and will yield a (-) and therefore be

    // less than zero

    // get the vector for the edge we are clipping

    Vector2 e = v2 - v1;

    // compute the location along e

    double u = d1 / (d1 - d2);

    e.multiply(u);

    e.add(v1);

    // add the point

    cp.add(e);

  }

}



// the edge vector

Vector2 refv = ref.edge;

refv.normalize();

double o1 = refv.dot(ref.v1);

// clip the incident edge by the first

// vertex of the reference edge

ClippedPoints cp = clip(inc.v1, inc.v2, refv, o1);

// if we dont have 2 points left then fail

if (cp.length < 2) return;

// clip whats left of the incident edge by the

// second vertex of the reference edge

// but we need to clip in the opposite direction

// so we flip the direction and offset

double o2 = refv.dot(ref.v2);

ClippedPoints cp = clip(cp[0], cp[1], -refv, -o2);

// if we dont have 2 points left then fail

if (cp.length < 2) return;

// get the reference edge normal

Vector2 refNorm = ref.cross(-1.0);

// if we had to flip the incident and reference edges

// then we need to flip the reference edge normal to

// clip properly

if (flip) refNorm.negate();

// get the largest depth

double max = refNorm.dot(ref.max);

// make sure the final points are not past this maximum

if (refNorm.dot(cp[0]) < max) {

  cp.remove(cp[0]);

}

if (refNorm.dot(cp[1]) - max < 0.0) {

  cp.remove(cp[1]);

}

// return the valid points

return cp;



