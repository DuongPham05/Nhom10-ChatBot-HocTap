// /*
// =============================================================
//   CÂU 3 (4,5 điểm): THIẾT LẬP NGUỒN SÁNG SPOTLIGHT
// =============================================================
//   Yêu cầu:
//   - Ít nhất 6 nguồn sáng Spotlight (KHÔNG dùng Point/Directional Light)
//   - Có luồng sáng hình nón, góc chiếu rộng
//   - Tắt Ambient toàn cục → cảnh tối ban đêm
//   - Mỗi luồng sáng khác màu (Đỏ, Xanh Dương, Vàng)
//   - Khi luồng sáng quét trúng mặt sàn → sàn sáng rực màu tương ứng
//   - Khi giàn đèn di chuyển lên xuống → luồng sáng di chuyển theo
//   - Khi đèn pha xoay → luồng sáng quét theo mặt sàn và không trung

//   Cấu hình:
//     GL_LIGHT0 (Đỏ):    đèn trên giàn, X=-3
//     GL_LIGHT1 (Xanh):  đèn trên giàn, X= 0
//     GL_LIGHT2 (Vàng):  đèn trên giàn, X=+3
//     GL_LIGHT3 (Đỏ):    đèn sàn, X=-3, Z=4.5, chiếu lên
//     GL_LIGHT4 (Xanh):  đèn sàn, X= 0, Z=4.5, chiếu lên
//     GL_LIGHT5 (Vàng):  đèn sàn, X=+3, Z=4.5, chiếu lên

//   COMPILE:
//     Windows: g++ cau3_lighting.cpp -o cau3 -lfreeglut -lopengl32 -lglu32
//     Linux:   g++ cau3_lighting.cpp -o cau3 -lGL -lGLU -lglut
//     macOS:   g++ cau3_lighting.cpp -o cau3 -framework OpenGL -framework GLUT
// =============================================================
// */

// #ifdef _WIN32
// #include <windows.h>
// #endif

// #include <GL/glut.h>
// #include <GL/glu.h>
// #include <cmath>
// #include <cstdio>

// #define PI 3.14159265358979323846f

// // ─── BIẾN TOÀN CỤC ───────────────────────────────────────────────
// float gTime      = 0.0f;
// float trussY     = 4.0f;
// float lampAngle[6] = {0, 0, 0, 0, 0, 0};

// // ─── VẼ KHỐI CƠ BẢN THỦ CÔNG ────────────────────────────────────
// void drawBox(float w, float h, float d) {
//     float hw = w*0.5f, hh = h*0.5f, hd = d*0.5f;
//     glBegin(GL_QUADS);
//         glNormal3f(0,0,1);
//         glVertex3f(-hw,-hh, hd); glVertex3f( hw,-hh, hd);
//         glVertex3f( hw, hh, hd); glVertex3f(-hw, hh, hd);
//         glNormal3f(0,0,-1);
//         glVertex3f( hw,-hh,-hd); glVertex3f(-hw,-hh,-hd);
//         glVertex3f(-hw, hh,-hd); glVertex3f( hw, hh,-hd);
//         glNormal3f(-1,0,0);
//         glVertex3f(-hw,-hh,-hd); glVertex3f(-hw,-hh, hd);
//         glVertex3f(-hw, hh, hd); glVertex3f(-hw, hh,-hd);
//         glNormal3f(1,0,0);
//         glVertex3f( hw,-hh, hd); glVertex3f( hw,-hh,-hd);
//         glVertex3f( hw, hh,-hd); glVertex3f( hw, hh, hd);
//         glNormal3f(0,1,0);
//         glVertex3f(-hw, hh, hd); glVertex3f( hw, hh, hd);
//         glVertex3f( hw, hh,-hd); glVertex3f(-hw, hh,-hd);
//         glNormal3f(0,-1,0);
//         glVertex3f(-hw,-hh,-hd); glVertex3f( hw,-hh,-hd);
//         glVertex3f( hw,-hh, hd); glVertex3f(-hw,-hh, hd);
//     glEnd();
// }

// void drawCylinder(float radius, float height, int slices) {
//     float step = 2.0f * PI / slices;
//     glBegin(GL_QUAD_STRIP);
//     for (int i = 0; i <= slices; i++) {
//         float a = i * step;
//         glNormal3f(cosf(a), 0, sinf(a));
//         glVertex3f(radius*cosf(a), 0,      radius*sinf(a));
//         glVertex3f(radius*cosf(a), height, radius*sinf(a));
//     }
//     glEnd();
//     glBegin(GL_TRIANGLE_FAN);
//     glNormal3f(0,1,0); glVertex3f(0,height,0);
//     for (int i=0; i<=slices; i++) {
//         float a=i*step;
//         glVertex3f(radius*cosf(a), height, radius*sinf(a));
//     }
//     glEnd();
//     glBegin(GL_TRIANGLE_FAN);
//     glNormal3f(0,-1,0); glVertex3f(0,0,0);
//     for (int i=slices; i>=0; i--) {
//         float a=i*step;
//         glVertex3f(radius*cosf(a), 0, radius*sinf(a));
//     }
//     glEnd();
// }

// void drawCone(float baseR, float topR, float height, int slices) {
//     float step = 2.0f * PI / slices;
//     glBegin(GL_QUAD_STRIP);
//     for (int i = 0; i <= slices; i++) {
//         float a = i * step;
//         float c = cosf(a), s = sinf(a);
//         glNormal3f(c, 0.3f, s);
//         glVertex3f(topR*c,    0,      topR*s);
//         glVertex3f(baseR*c, -height, baseR*s);
//     }
//     glEnd();
// }

// // ─── MẶT SÀN: vật liệu sáng để nhận ánh đèn Spotlight rõ ────────
// //   QUAN TRỌNG: diffuse đủ cao để ánh sáng từ Spotlight chiếu rõ
// void drawStageFloor() {
//     // Vật liệu sàn: diffuse sáng hơn để nhận màu từ Spotlight
//     GLfloat mat_amb[] = {0.02f, 0.02f, 0.02f, 1.0f};
//     GLfloat mat_dif[] = {0.8f,  0.8f,  0.8f,  1.0f};  // Cao để nhận ánh sáng
//     GLfloat mat_spe[] = {0.5f,  0.5f,  0.5f,  1.0f};
//     GLfloat mat_shi[] = {80.0f};
//     glMaterialfv(GL_FRONT, GL_AMBIENT,   mat_amb);
//     glMaterialfv(GL_FRONT, GL_DIFFUSE,   mat_dif);
//     glMaterialfv(GL_FRONT, GL_SPECULAR,  mat_spe);
//     glMaterialfv(GL_FRONT, GL_SHININESS, mat_shi);

//     glNormal3f(0, 1, 0);
//     glBegin(GL_QUADS);
//         glVertex3f(-6.0f, 0.0f, -5.0f);
//         glVertex3f( 6.0f, 0.0f, -5.0f);
//         glVertex3f( 6.0f, 0.0f,  5.0f);
//         glVertex3f(-6.0f, 0.0f,  5.0f);
//     glEnd();

//     // Grid
//     glDisable(GL_LIGHTING);
//     glColor3f(0.15f, 0.15f, 0.15f);
//     glBegin(GL_LINES);
//     for (int x = -6; x <= 6; x++) {
//         glVertex3f((float)x, 0.01f, -5.0f);
//         glVertex3f((float)x, 0.01f,  5.0f);
//     }
//     for (int z = -5; z <= 5; z++) {
//         glVertex3f(-6.0f, 0.01f, (float)z);
//         glVertex3f( 6.0f, 0.01f, (float)z);
//     }
//     glEnd();
//     glEnable(GL_LIGHTING);
// }

// // ─── GIÀN ĐÈN ────────────────────────────────────────────────────
// void drawTruss() {
//     GLfloat mat_amb[] = {0.2f, 0.2f, 0.2f, 1.0f};
//     GLfloat mat_dif[] = {0.5f, 0.5f, 0.5f, 1.0f};
//     GLfloat mat_spe[] = {0.8f, 0.8f, 0.8f, 1.0f};
//     GLfloat mat_shi[] = {80.0f};
//     glMaterialfv(GL_FRONT, GL_AMBIENT,   mat_amb);
//     glMaterialfv(GL_FRONT, GL_DIFFUSE,   mat_dif);
//     glMaterialfv(GL_FRONT, GL_SPECULAR,  mat_spe);
//     glMaterialfv(GL_FRONT, GL_SHININESS, mat_shi);

//     glPushMatrix();
//         glTranslatef(-4.5f, 0.0f, 0.0f);
//         drawCylinder(0.12f, trussY, 12);
//     glPopMatrix();
//     glPushMatrix();
//         glTranslatef(4.5f, 0.0f, 0.0f);
//         drawCylinder(0.12f, trussY, 12);
//     glPopMatrix();
//     glPushMatrix();
//         glTranslatef(0.0f, trussY, 0.0f);
//         drawBox(9.2f, 0.2f, 0.2f);
//     glPopMatrix();
// }

// // ─── VẼ THÂN ĐÈN + HÌNH NÓN PHÁT SÁNG (trên giàn) ───────────────
// void drawTrussSpotBody(float r, float g, float b, float angle) {
//     glPushMatrix();
//         glRotatef(angle, 0.0f, 1.0f, 0.0f);

//         // Thân hộp
//         GLfloat body_amb[] = {0.3f, 0.3f, 0.3f, 1.0f};
//         GLfloat body_dif[] = {0.6f, 0.6f, 0.6f, 1.0f};
//         GLfloat body_spe[] = {1.0f, 1.0f, 1.0f, 1.0f};
//         GLfloat body_shi[] = {100.0f};
//         glMaterialfv(GL_FRONT, GL_AMBIENT,   body_amb);
//         glMaterialfv(GL_FRONT, GL_DIFFUSE,   body_dif);
//         glMaterialfv(GL_FRONT, GL_SPECULAR,  body_spe);
//         glMaterialfv(GL_FRONT, GL_SHININESS, body_shi);
//         drawBox(0.3f, 0.3f, 0.3f);

//         // Hình nón phát sáng (emission) chiếu xuống
//         GLfloat em[]  = {r * 0.9f, g * 0.9f, b * 0.9f, 1.0f};
//         GLfloat dif[] = {r, g, b, 0.4f};
//         glMaterialfv(GL_FRONT, GL_EMISSION, em);
//         glMaterialfv(GL_FRONT, GL_DIFFUSE,  dif);
//         glEnable(GL_BLEND);
//         glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
//         glPushMatrix();
//             glTranslatef(0, -0.15f, 0);
//             drawCone(0.8f, 0.15f, 1.8f, 16);
//         glPopMatrix();
//         glDisable(GL_BLEND);
//         GLfloat zero[] = {0,0,0,1};
//         glMaterialfv(GL_FRONT, GL_EMISSION, zero);
//     glPopMatrix();
// }

// // ─── VẼ THÂN ĐÈN + HÌNH NÓN PHÁT SÁNG (sàn, chiếu lên) ──────────
// void drawFloorSpotBody(float r, float g, float b, float angle) {
//     glPushMatrix();
//         glRotatef(angle, 0.0f, 1.0f, 0.0f);

//         GLfloat body_amb[] = {0.3f, 0.3f, 0.3f, 1.0f};
//         GLfloat body_dif[] = {0.6f, 0.6f, 0.6f, 1.0f};
//         glMaterialfv(GL_FRONT, GL_AMBIENT, body_amb);
//         glMaterialfv(GL_FRONT, GL_DIFFUSE, body_dif);
//         drawBox(0.25f, 0.25f, 0.25f);

//         GLfloat em[]  = {r*0.9f, g*0.9f, b*0.9f, 1.0f};
//         GLfloat dif[] = {r, g, b, 0.35f};
//         glMaterialfv(GL_FRONT, GL_EMISSION, em);
//         glMaterialfv(GL_FRONT, GL_DIFFUSE,  dif);
//         glEnable(GL_BLEND);
//         glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
//         glPushMatrix();
//             glTranslatef(0, 0.125f, 0);
//             glRotatef(180.0f, 1.0f, 0.0f, 0.0f);
//             drawCone(1.5f, 0.15f, 3.5f, 16);
//         glPopMatrix();
//         glDisable(GL_BLEND);
//         GLfloat zero[] = {0,0,0,1};
//         glMaterialfv(GL_FRONT, GL_EMISSION, zero);
//     glPopMatrix();
// }

// // ─── THIẾT LẬP 6 NGUỒN SÁNG SPOTLIGHT ───────────────────────────
// //
// //  Câu 3: setupLights() là phần CỐT LÕI của câu này.
// //
// //  Nguyên lý:
// //  - GL_SPOT_CUTOFF: góc hình nón (< 90 độ) → đây là SPOTLIGHT
// //  - GL_SPOT_DIRECTION: hướng chiếu, xoay theo lampAngle để quét
// //  - GL_POSITION với W=1: positional light (không phải directional)
// //  - Diffuse màu = màu sắc luồng sáng
// //  - Ambient = 0 để cảnh tối như ban đêm
// //
// //  Đèn trên giàn (0,1,2): chiếu xuống sàn
// //    - Vị trí di chuyển theo trussY (giàn lên/xuống → đèn di chuyển)
// //    - Hướng xoay theo lampAngle[i] → quét theo mặt sàn
// //
// //  Đèn sàn (3,4,5): chiếu lên không trung
// //    - Hướng xoay theo lampAngle[i+3] → quét lên không trung
// //
// void setupLights() {
//     // Tắt ambient toàn cục (ban đêm)
//     GLfloat zero[] = {0.0f, 0.0f, 0.0f, 1.0f};
//     glLightModelfv(GL_LIGHT_MODEL_AMBIENT, zero);

//     // ── ĐÈN TRÊN GIÀN (GL_LIGHT0, 1, 2) ──
//     struct TrussLamp {
//         float ox;      // offset X trên thanh ngang
//         float r, g, b;
//         GLenum gl;
//     } tl[3] = {
//         {-3.0f, 1.0f, 0.0f, 0.0f, GL_LIGHT0},   // Đỏ
//         { 0.0f, 0.0f, 0.4f, 1.0f, GL_LIGHT1},   // Xanh dương
//         { 3.0f, 1.0f, 1.0f, 0.0f, GL_LIGHT2},   // Vàng
//     };

//     for (int i = 0; i < 3; i++) {
//         float rad = lampAngle[i] * PI / 180.0f;

//         // Vị trí đèn treo dưới thanh ngang → DI CHUYỂN THEO trussY
//         GLfloat pos[] = {tl[i].ox, trussY - 0.15f, 0.0f, 1.0f};

//         // Hướng chiếu xuống + xoay theo lampAngle → QUÉT THEO SÀN
//         GLfloat dir[] = {sinf(rad) * 0.8f, -1.0f, cosf(rad) * 0.3f};

//         glLightfv(tl[i].gl, GL_POSITION,       pos);
//         glLightfv(tl[i].gl, GL_SPOT_DIRECTION, dir);
//         glLightf (tl[i].gl, GL_SPOT_CUTOFF,    30.0f);   // Góc hình nón 30°
//         glLightf (tl[i].gl, GL_SPOT_EXPONENT,  10.0f);   // Độ tập trung
//         glLightf (tl[i].gl, GL_CONSTANT_ATTENUATION,  1.0f);
//         glLightf (tl[i].gl, GL_LINEAR_ATTENUATION,    0.05f);
//         glLightf (tl[i].gl, GL_QUADRATIC_ATTENUATION, 0.01f);

//         GLfloat dif[] = {tl[i].r, tl[i].g, tl[i].b, 1.0f};
//         GLfloat spe[] = {tl[i].r*0.5f, tl[i].g*0.5f, tl[i].b*0.5f, 1.0f};
//         glLightfv(tl[i].gl, GL_AMBIENT,  zero);
//         glLightfv(tl[i].gl, GL_DIFFUSE,  dif);
//         glLightfv(tl[i].gl, GL_SPECULAR, spe);
//         glEnable(tl[i].gl);
//     }

//     // ── ĐÈN SÀN (GL_LIGHT3, 4, 5) ──
//     struct FloorLamp {
//         float fx, fz;
//         float r, g, b;
//         GLenum gl;
//     } fl[3] = {
//         {-3.0f, 4.5f, 1.0f, 0.0f, 0.0f, GL_LIGHT3},   // Đỏ
//         { 0.0f, 4.5f, 0.0f, 0.4f, 1.0f, GL_LIGHT4},   // Xanh
//         { 3.0f, 4.5f, 1.0f, 1.0f, 0.0f, GL_LIGHT5},   // Vàng
//     };

//     for (int i = 0; i < 3; i++) {
//         float rad = lampAngle[i + 3] * PI / 180.0f;

//         GLfloat pos[] = {fl[i].fx, 0.13f, fl[i].fz, 1.0f};

//         // Hướng chiếu lên + xoay → QUÉT TRÊN KHÔNG TRUNG
//         GLfloat dir[] = {sinf(rad) * 0.4f, 1.0f, cosf(rad) * 0.2f};

//         glLightfv(fl[i].gl, GL_POSITION,       pos);
//         glLightfv(fl[i].gl, GL_SPOT_DIRECTION, dir);
//         glLightf (fl[i].gl, GL_SPOT_CUTOFF,    25.0f);   // Góc hình nón 25°
//         glLightf (fl[i].gl, GL_SPOT_EXPONENT,  6.0f);
//         glLightf (fl[i].gl, GL_CONSTANT_ATTENUATION,  1.0f);
//         glLightf (fl[i].gl, GL_LINEAR_ATTENUATION,    0.02f);
//         glLightf (fl[i].gl, GL_QUADRATIC_ATTENUATION, 0.005f);

//         GLfloat dif[] = {fl[i].r, fl[i].g, fl[i].b, 1.0f};
//         glLightfv(fl[i].gl, GL_AMBIENT,  zero);
//         glLightfv(fl[i].gl, GL_DIFFUSE,  dif);
//         glLightfv(fl[i].gl, GL_SPECULAR, zero);
//         glEnable(fl[i].gl);
//     }
// }

// // ─── IDLE ─────────────────────────────────────────────────────────
// void idle() {
//     const float dt = 0.016f;
//     gTime += dt;
//     trussY = 4.0f + sinf(gTime * 0.8f) * 1.0f;
//     for (int i = 0; i < 6; i++) {
//         float speed = (i < 3) ? 60.0f : 45.0f;
//         lampAngle[i] += speed * dt;
//         if (lampAngle[i] >= 360.0f) lampAngle[i] -= 360.0f;
//     }
//     glutPostRedisplay();
// }

// // ─── DISPLAY ──────────────────────────────────────────────────────
// void display() {
//     glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
//     glLoadIdentity();

//     gluLookAt(0.0, 8.0, 12.0,
//               0.0, 2.0,  0.0,
//               0.0, 1.0,  0.0);

//     // CẬP NHẬT 6 SPOTLIGHT
//     setupLights();

//     // Sàn (vật liệu nhận ánh sáng Spotlight)
//     drawStageFloor();

//     // Giàn đèn
//     drawTruss();

//     // 3 đèn trên giàn
//     float trussColors[3][3] = {
//         {1.0f, 0.0f, 0.0f},
//         {0.0f, 0.4f, 1.0f},
//         {1.0f, 1.0f, 0.0f},
//     };
//     float trussOffsets[3] = {-3.0f, 0.0f, 3.0f};
//     for (int i = 0; i < 3; i++) {
//         glPushMatrix();
//             glTranslatef(trussOffsets[i], trussY - 0.15f, 0.0f);
//             drawTrussSpotBody(trussColors[i][0], trussColors[i][1], trussColors[i][2],
//                               lampAngle[i]);
//         glPopMatrix();
//     }

//     // 3 đèn sàn
//     float floorX[3] = {-3.0f, 0.0f, 3.0f};
//     float floorColors[3][3] = {
//         {1.0f, 0.0f, 0.0f},
//         {0.0f, 0.4f, 1.0f},
//         {1.0f, 1.0f, 0.0f},
//     };
//     for (int i = 0; i < 3; i++) {
//         glPushMatrix();
//             glTranslatef(floorX[i], 0.0f, 4.5f);
//             drawFloorSpotBody(floorColors[i][0], floorColors[i][1], floorColors[i][2],
//                               lampAngle[i + 3]);
//         glPopMatrix();
//     }

//     glutSwapBuffers();
// }

// // ─── RESHAPE ──────────────────────────────────────────────────────
// void reshape(int w, int h) {
//     if (h == 0) h = 1;
//     glViewport(0, 0, w, h);
//     glMatrixMode(GL_PROJECTION);
//     glLoadIdentity();
//     gluPerspective(60.0, (double)w / h, 0.1, 100.0);
//     glMatrixMode(GL_MODELVIEW);
//     glLoadIdentity();
// }

// void keyboard(unsigned char key, int x, int y) {
//     if (key == 27) exit(0);
// }

// // ─── INIT ─────────────────────────────────────────────────────────
// void init() {
//     glClearColor(0.0f, 0.0f, 0.02f, 1.0f);
//     glEnable(GL_DEPTH_TEST);
//     glEnable(GL_LIGHTING);
//     glEnable(GL_NORMALIZE);
//     glShadeModel(GL_SMOOTH);

//     // Bật 6 Spotlight
//     glEnable(GL_LIGHT0); glEnable(GL_LIGHT1); glEnable(GL_LIGHT2);
//     glEnable(GL_LIGHT3); glEnable(GL_LIGHT4); glEnable(GL_LIGHT5);

//     // Tắt ambient toàn cục
//     GLfloat zero[] = {0.0f, 0.0f, 0.0f, 1.0f};
//     glLightModelfv(GL_LIGHT_MODEL_AMBIENT, zero);
// }

// int main(int argc, char** argv) {
//     glutInit(&argc, argv);
//     glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH);
//     glutInitWindowSize(1024, 768);
//     glutInitWindowPosition(100, 100);
//     glutCreateWindow("Cau 3 - He Thong 6 Spotlight");

//     init();

//     glutDisplayFunc(display);
//     glutReshapeFunc(reshape);
//     glutKeyboardFunc(keyboard);
//     glutIdleFunc(idle);

//     printf("=== CAU 3: 6 NGUON SANG SPOTLIGHT ===\n");
//     printf("GL_LIGHT0 (Do)   - tren gian X=-3, chieu xuong\n");
//     printf("GL_LIGHT1 (Xanh) - tren gian X= 0, chieu xuong\n");
//     printf("GL_LIGHT2 (Vang) - tren gian X=+3, chieu xuong\n");
//     printf("GL_LIGHT3 (Do)   - san X=-3, Z=4.5, chieu len\n");
//     printf("GL_LIGHT4 (Xanh) - san X= 0, Z=4.5, chieu len\n");
//     printf("GL_LIGHT5 (Vang) - san X=+3, Z=4.5, chieu len\n");
//     printf("Ambient toan cuc = 0 (ban dem)\n");
//     printf("ESC: Thoat\n");

//     glutMainLoop();
//     return 0;
// }
