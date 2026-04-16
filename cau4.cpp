// /*
// =============================================================
//   CÂU 4 (0,5 điểm): TƯƠNG TÁC BÀN PHÍM
// =============================================================
//   Yêu cầu:
//   - Phím R/r: Bật/tắt luồng sáng màu Đỏ  (đèn 1 + đèn 4)
//   - Phím G/g: Bật/tắt luồng sáng màu Xanh Dương (đèn 2 + đèn 5)
//   - Phím B/b: Bật/tắt luồng sáng màu Vàng (đèn 3 + đèn 6)
//   - Phím 1-6: Dừng/tiếp tục xoay đèn tương ứng
//   - Phím ESC: Thoát

//   File này là phiên bản HOÀN CHỈNH tích hợp tất cả câu 1-4.

//   COMPILE:
//     Windows: g++ cau4_keyboard.cpp -o cau4 -lfreeglut -lopengl32 -lglu32
//     Linux:   g++ cau4_keyboard.cpp -o cau4 -lGL -lGLU -lglut
//     macOS:   g++ cau4_keyboard.cpp -o cau4 -framework OpenGL -framework GLUT
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
// float lampAngle[6]    = {0, 0, 0, 0, 0, 0};
// bool  lampSpinning[6] = {true, true, true, true, true, true};

// // Câu 4: Trạng thái bật/tắt theo màu
// bool redOn    = true;   // Điều khiển bằng R/r
// bool greenOn  = true;   // Điều khiển bằng G/g
// bool yellowOn = true;   // Điều khiển bằng B/b

// // ─── CÁC HÀM VẼ ─────────────────────────────────────────────────
// void drawBox(float w, float h, float d) {
//     float hw=w*0.5f, hh=h*0.5f, hd=d*0.5f;
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
//         float a = i*step;
//         glNormal3f(cosf(a), 0, sinf(a));
//         glVertex3f(radius*cosf(a), 0,      radius*sinf(a));
//         glVertex3f(radius*cosf(a), height, radius*sinf(a));
//     }
//     glEnd();
//     glBegin(GL_TRIANGLE_FAN);
//     glNormal3f(0,1,0); glVertex3f(0,height,0);
//     for (int i=0; i<=slices; i++) {
//         float a=i*step;
//         glVertex3f(radius*cosf(a),height,radius*sinf(a));
//     }
//     glEnd();
//     glBegin(GL_TRIANGLE_FAN);
//     glNormal3f(0,-1,0); glVertex3f(0,0,0);
//     for (int i=slices; i>=0; i--) {
//         float a=i*step;
//         glVertex3f(radius*cosf(a),0,radius*sinf(a));
//     }
//     glEnd();
// }

// void drawCone(float baseR, float topR, float height, int slices) {
//     float step = 2.0f * PI / slices;
//     glBegin(GL_QUAD_STRIP);
//     for (int i = 0; i <= slices; i++) {
//         float a=i*step; float c=cosf(a), s=sinf(a);
//         glNormal3f(c, 0.3f, s);
//         glVertex3f(topR*c,    0,      topR*s);
//         glVertex3f(baseR*c, -height, baseR*s);
//     }
//     glEnd();
// }

// // ─── MẶT SÀN ─────────────────────────────────────────────────────
// void drawStageFloor() {
//     GLfloat mat_amb[] = {0.02f, 0.02f, 0.02f, 1.0f};
//     GLfloat mat_dif[] = {0.8f,  0.8f,  0.8f,  1.0f};
//     GLfloat mat_spe[] = {0.5f,  0.5f,  0.5f,  1.0f};
//     GLfloat mat_shi[] = {80.0f};
//     glMaterialfv(GL_FRONT, GL_AMBIENT,   mat_amb);
//     glMaterialfv(GL_FRONT, GL_DIFFUSE,   mat_dif);
//     glMaterialfv(GL_FRONT, GL_SPECULAR,  mat_spe);
//     glMaterialfv(GL_FRONT, GL_SHININESS, mat_shi);
//     glNormal3f(0, 1, 0);
//     glBegin(GL_QUADS);
//         glVertex3f(-6.0f, 0.0f, -5.0f); glVertex3f( 6.0f, 0.0f, -5.0f);
//         glVertex3f( 6.0f, 0.0f,  5.0f); glVertex3f(-6.0f, 0.0f,  5.0f);
//     glEnd();
//     glDisable(GL_LIGHTING);
//     glColor3f(0.15f, 0.15f, 0.15f);
//     glBegin(GL_LINES);
//     for (int x=-6; x<=6; x++) {
//         glVertex3f((float)x, 0.01f,-5.0f); glVertex3f((float)x, 0.01f, 5.0f);
//     }
//     for (int z=-5; z<=5; z++) {
//         glVertex3f(-6.0f, 0.01f,(float)z); glVertex3f( 6.0f, 0.01f,(float)z);
//     }
//     glEnd();
//     glEnable(GL_LIGHTING);
// }

// // ─── GIÀN ĐÈN ─────────────────────────────────────────────────────
// void drawTruss() {
//     GLfloat mat_amb[] = {0.2f,0.2f,0.2f,1.0f};
//     GLfloat mat_dif[] = {0.5f,0.5f,0.5f,1.0f};
//     GLfloat mat_spe[] = {0.8f,0.8f,0.8f,1.0f};
//     GLfloat mat_shi[] = {80.0f};
//     glMaterialfv(GL_FRONT,GL_AMBIENT,   mat_amb);
//     glMaterialfv(GL_FRONT,GL_DIFFUSE,   mat_dif);
//     glMaterialfv(GL_FRONT,GL_SPECULAR,  mat_spe);
//     glMaterialfv(GL_FRONT,GL_SHININESS, mat_shi);
//     glPushMatrix();
//         glTranslatef(-4.5f,0,0); drawCylinder(0.12f,trussY,12);
//     glPopMatrix();
//     glPushMatrix();
//         glTranslatef(4.5f,0,0); drawCylinder(0.12f,trussY,12);
//     glPopMatrix();
//     glPushMatrix();
//         glTranslatef(0,trussY,0); drawBox(9.2f,0.2f,0.2f);
//     glPopMatrix();
// }

// // ─── ĐÈN TRÊN GIÀN ────────────────────────────────────────────────
// void drawTrussSpotBody(float r, float g, float b, float angle, bool isOn) {
//     glPushMatrix();
//         glRotatef(angle, 0,1,0);
//         GLfloat ba[]={0.3f,0.3f,0.3f,1.0f}, bd[]={0.6f,0.6f,0.6f,1.0f};
//         GLfloat bs[]={1.0f,1.0f,1.0f,1.0f}, bsh[]={100.0f};
//         glMaterialfv(GL_FRONT,GL_AMBIENT,  ba);
//         glMaterialfv(GL_FRONT,GL_DIFFUSE,  bd);
//         glMaterialfv(GL_FRONT,GL_SPECULAR, bs);
//         glMaterialfv(GL_FRONT,GL_SHININESS,bsh);
//         drawBox(0.3f,0.3f,0.3f);
//         if (isOn) {
//             GLfloat em[]={r*0.9f,g*0.9f,b*0.9f,1.0f};
//             GLfloat cd[]={r,g,b,0.4f};
//             glMaterialfv(GL_FRONT,GL_EMISSION,em);
//             glMaterialfv(GL_FRONT,GL_DIFFUSE, cd);
//             glEnable(GL_BLEND);
//             glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);
//             glPushMatrix();
//                 glTranslatef(0,-0.15f,0);
//                 drawCone(0.8f,0.15f,1.8f,16);
//             glPopMatrix();
//             glDisable(GL_BLEND);
//             GLfloat ze[]={0,0,0,1};
//             glMaterialfv(GL_FRONT,GL_EMISSION,ze);
//         }
//     glPopMatrix();
// }

// // ─── ĐÈN SÀN ──────────────────────────────────────────────────────
// void drawFloorSpotBody(float r, float g, float b, float angle, bool isOn) {
//     glPushMatrix();
//         glRotatef(angle,0,1,0);
//         GLfloat ba[]={0.3f,0.3f,0.3f,1.0f}, bd[]={0.6f,0.6f,0.6f,1.0f};
//         glMaterialfv(GL_FRONT,GL_AMBIENT,ba);
//         glMaterialfv(GL_FRONT,GL_DIFFUSE,bd);
//         drawBox(0.25f,0.25f,0.25f);
//         if (isOn) {
//             GLfloat em[]={r*0.9f,g*0.9f,b*0.9f,1.0f};
//             GLfloat cd[]={r,g,b,0.35f};
//             glMaterialfv(GL_FRONT,GL_EMISSION,em);
//             glMaterialfv(GL_FRONT,GL_DIFFUSE, cd);
//             glEnable(GL_BLEND);
//             glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);
//             glPushMatrix();
//                 glTranslatef(0,0.125f,0);
//                 glRotatef(180.0f,1,0,0);
//                 drawCone(1.5f,0.15f,3.5f,16);
//             glPopMatrix();
//             glDisable(GL_BLEND);
//             GLfloat ze[]={0,0,0,1};
//             glMaterialfv(GL_FRONT,GL_EMISSION,ze);
//         }
//     glPopMatrix();
// }

// // ─── THIẾT LẬP 6 SPOTLIGHT CÓ ĐIỀU KHIỂN BẬT/TẮT ────────────────
// //   Câu 4: Khi redOn/greenOn/yellowOn = false →
// //          diffuse = (0,0,0) và glDisable đèn tương ứng
// void setupLights() {
//     GLfloat zero[] = {0,0,0,1};
//     glLightModelfv(GL_LIGHT_MODEL_AMBIENT, zero);

//     struct TrussLamp {
//         float ox; float r,g,b; bool* on; GLenum gl;
//     } tl[3] = {
//         {-3.0f, 1.0f, 0.0f, 0.0f, &redOn,    GL_LIGHT0},
//         { 0.0f, 0.0f, 0.4f, 1.0f, &greenOn,  GL_LIGHT1},
//         { 3.0f, 1.0f, 1.0f, 0.0f, &yellowOn, GL_LIGHT2},
//     };
//     for (int i = 0; i < 3; i++) {
//         float rad = lampAngle[i] * PI / 180.0f;
//         GLfloat pos[] = {tl[i].ox, trussY - 0.15f, 0.0f, 1.0f};
//         GLfloat dir[] = {sinf(rad)*0.8f, -1.0f, cosf(rad)*0.3f};
//         glLightfv(tl[i].gl, GL_POSITION,       pos);
//         glLightfv(tl[i].gl, GL_SPOT_DIRECTION, dir);
//         glLightf (tl[i].gl, GL_SPOT_CUTOFF,    30.0f);
//         glLightf (tl[i].gl, GL_SPOT_EXPONENT,  10.0f);
//         glLightf (tl[i].gl, GL_CONSTANT_ATTENUATION,  1.0f);
//         glLightf (tl[i].gl, GL_LINEAR_ATTENUATION,    0.05f);
//         glLightf (tl[i].gl, GL_QUADRATIC_ATTENUATION, 0.01f);
//         bool on = *(tl[i].on);
//         GLfloat dif[] = {on?tl[i].r:0.0f, on?tl[i].g:0.0f, on?tl[i].b:0.0f, 1.0f};
//         GLfloat spe[] = {on?tl[i].r*0.5f:0.0f, on?tl[i].g*0.5f:0.0f, on?tl[i].b*0.5f:0.0f, 1.0f};
//         glLightfv(tl[i].gl, GL_AMBIENT,  zero);
//         glLightfv(tl[i].gl, GL_DIFFUSE,  dif);
//         glLightfv(tl[i].gl, GL_SPECULAR, spe);
//         if (on) glEnable(tl[i].gl); else glDisable(tl[i].gl);
//     }

//     struct FloorLamp {
//         float fx, fz; float r,g,b; bool* on; GLenum gl;
//     } fl[3] = {
//         {-3.0f, 4.5f, 1.0f, 0.0f, 0.0f, &redOn,    GL_LIGHT3},
//         { 0.0f, 4.5f, 0.0f, 0.4f, 1.0f, &greenOn,  GL_LIGHT4},
//         { 3.0f, 4.5f, 1.0f, 1.0f, 0.0f, &yellowOn, GL_LIGHT5},
//     };
//     for (int i = 0; i < 3; i++) {
//         float rad = lampAngle[i+3] * PI / 180.0f;
//         GLfloat pos[] = {fl[i].fx, 0.13f, fl[i].fz, 1.0f};
//         GLfloat dir[] = {sinf(rad)*0.4f, 1.0f, cosf(rad)*0.2f};
//         glLightfv(fl[i].gl, GL_POSITION,       pos);
//         glLightfv(fl[i].gl, GL_SPOT_DIRECTION, dir);
//         glLightf (fl[i].gl, GL_SPOT_CUTOFF,    25.0f);
//         glLightf (fl[i].gl, GL_SPOT_EXPONENT,  6.0f);
//         glLightf (fl[i].gl, GL_CONSTANT_ATTENUATION,  1.0f);
//         glLightf (fl[i].gl, GL_LINEAR_ATTENUATION,    0.02f);
//         glLightf (fl[i].gl, GL_QUADRATIC_ATTENUATION, 0.005f);
//         bool on = *(fl[i].on);
//         GLfloat dif[] = {on?fl[i].r:0.0f, on?fl[i].g:0.0f, on?fl[i].b:0.0f, 1.0f};
//         glLightfv(fl[i].gl, GL_AMBIENT,  zero);
//         glLightfv(fl[i].gl, GL_DIFFUSE,  dif);
//         glLightfv(fl[i].gl, GL_SPECULAR, zero);
//         if (on) glEnable(fl[i].gl); else glDisable(fl[i].gl);
//     }
// }

// // ─── CÂU 4: XỬ LÝ BÀN PHÍM ───────────────────────────────────────
// void keyboard(unsigned char key, int x, int y) {
//     switch (key) {
//         // Bật/tắt màu Đỏ (đèn 1 trên giàn + đèn 4 sàn)
//         case 'R': case 'r':
//             redOn = !redOn;
//             printf("Den Do (1+4): %s\n", redOn ? "BAT" : "TAT");
//             break;
//         // Bật/tắt màu Xanh Dương (đèn 2 trên giàn + đèn 5 sàn)
//         case 'G': case 'g':
//             greenOn = !greenOn;
//             printf("Den Xanh (2+5): %s\n", greenOn ? "BAT" : "TAT");
//             break;
//         // Bật/tắt màu Vàng (đèn 3 trên giàn + đèn 6 sàn)
//         case 'B': case 'b':
//             yellowOn = !yellowOn;
//             printf("Den Vang (3+6): %s\n", yellowOn ? "BAT" : "TAT");
//             break;
//         // Dừng/tiếp tục xoay từng đèn
//         case '1': lampSpinning[0] = !lampSpinning[0];
//                   printf("Den 1 (tren gian, Do):    %s\n", lampSpinning[0]?"XOAY":"DUNG"); break;
//         case '2': lampSpinning[1] = !lampSpinning[1];
//                   printf("Den 2 (tren gian, Xanh):  %s\n", lampSpinning[1]?"XOAY":"DUNG"); break;
//         case '3': lampSpinning[2] = !lampSpinning[2];
//                   printf("Den 3 (tren gian, Vang):  %s\n", lampSpinning[2]?"XOAY":"DUNG"); break;
//         case '4': lampSpinning[3] = !lampSpinning[3];
//                   printf("Den 4 (san, Do):          %s\n", lampSpinning[3]?"XOAY":"DUNG"); break;
//         case '5': lampSpinning[4] = !lampSpinning[4];
//                   printf("Den 5 (san, Xanh):        %s\n", lampSpinning[4]?"XOAY":"DUNG"); break;
//         case '6': lampSpinning[5] = !lampSpinning[5];
//                   printf("Den 6 (san, Vang):        %s\n", lampSpinning[5]?"XOAY":"DUNG"); break;
//         case 27: exit(0); break;
//     }
//     glutPostRedisplay();
// }

// // ─── IDLE ─────────────────────────────────────────────────────────
// void idle() {
//     const float dt = 0.016f;
//     gTime += dt;
//     trussY = 4.0f + sinf(gTime * 0.8f) * 1.0f;
//     for (int i = 0; i < 6; i++) {
//         // Chỉ xoay nếu lampSpinning[i] = true (Câu 4: phím 1-6 điều khiển)
//         if (lampSpinning[i]) {
//             float speed = (i < 3) ? 60.0f : 45.0f;
//             lampAngle[i] += speed * dt;
//             if (lampAngle[i] >= 360.0f) lampAngle[i] -= 360.0f;
//         }
//     }
//     glutPostRedisplay();
// }

// // ─── DISPLAY ──────────────────────────────────────────────────────
// void display() {
//     glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
//     glLoadIdentity();
//     gluLookAt(0.0, 8.0, 12.0, 0.0, 2.0, 0.0, 0.0, 1.0, 0.0);

//     setupLights();
//     drawStageFloor();
//     drawTruss();

//     // Dữ liệu đèn trên giàn
//     float tc[3][3] = { {1,0,0}, {0,0.4f,1}, {1,1,0} };
//     float to[3]    = { -3.0f, 0.0f, 3.0f };
//     bool* ton[3]   = { &redOn, &greenOn, &yellowOn };
//     for (int i = 0; i < 3; i++) {
//         glPushMatrix();
//             glTranslatef(to[i], trussY - 0.15f, 0.0f);
//             drawTrussSpotBody(tc[i][0], tc[i][1], tc[i][2],
//                               lampAngle[i], *(ton[i]));
//         glPopMatrix();
//     }

//     // Dữ liệu đèn sàn
//     float fx[3] = { -3.0f, 0.0f, 3.0f };
//     bool* fon[3] = { &redOn, &greenOn, &yellowOn };
//     for (int i = 0; i < 3; i++) {
//         glPushMatrix();
//             glTranslatef(fx[i], 0.0f, 4.5f);
//             drawFloorSpotBody(tc[i][0], tc[i][1], tc[i][2],
//                               lampAngle[i + 3], *(fon[i]));
//         glPopMatrix();
//     }

//     // ── HUD: Hiển thị trạng thái bàn phím ──
//     glDisable(GL_LIGHTING);
//     glMatrixMode(GL_PROJECTION);
//     glPushMatrix();
//         glLoadIdentity();
//         gluOrtho2D(0, 1024, 0, 768);
//         glMatrixMode(GL_MODELVIEW);
//         glPushMatrix();
//             glLoadIdentity();

//             // Tiêu đề HUD
//             glColor3f(1.0f, 1.0f, 0.5f);
//             glRasterPos2i(10, 745);
//             const char* title = "PHIM DIEU KHIEN:";
//             for (int i = 0; title[i]; i++) glutBitmapCharacter(GLUT_BITMAP_8_BY_13, title[i]);

//             // Màu đỏ
//             glColor3f(redOn ? 1.0f : 0.4f, 0.2f, 0.2f);
//             glRasterPos2i(10, 728);
//             char buf[64];
//             snprintf(buf, sizeof(buf), "R - Den Do  (1+4): %s", redOn ? "BAT" : "TAT");
//             for (int i = 0; buf[i]; i++) glutBitmapCharacter(GLUT_BITMAP_8_BY_13, buf[i]);

//             // Màu xanh
//             glColor3f(0.2f, greenOn ? 0.6f : 0.3f, greenOn ? 1.0f : 0.4f);
//             glRasterPos2i(10, 711);
//             snprintf(buf, sizeof(buf), "G - Den Xanh(2+5): %s", greenOn ? "BAT" : "TAT");
//             for (int i = 0; buf[i]; i++) glutBitmapCharacter(GLUT_BITMAP_8_BY_13, buf[i]);

//             // Màu vàng
//             glColor3f(yellowOn ? 1.0f : 0.4f, yellowOn ? 1.0f : 0.4f, 0.0f);
//             glRasterPos2i(10, 694);
//             snprintf(buf, sizeof(buf), "B - Den Vang(3+6): %s", yellowOn ? "BAT" : "TAT");
//             for (int i = 0; buf[i]; i++) glutBitmapCharacter(GLUT_BITMAP_8_BY_13, buf[i]);

//             // Trạng thái xoay từng đèn
//             glColor3f(0.8f, 0.8f, 0.8f);
//             glRasterPos2i(10, 672);
//             const char* spinTitle = "Xoay den (1-6):";
//             for (int i = 0; spinTitle[i]; i++) glutBitmapCharacter(GLUT_BITMAP_8_BY_13, spinTitle[i]);

//             for (int i = 0; i < 6; i++) {
//                 glColor3f(lampSpinning[i] ? 0.4f : 0.8f,
//                           lampSpinning[i] ? 0.8f : 0.4f, 0.4f);
//                 glRasterPos2i(10, 655 - i * 14);
//                 const char* names[6] = {
//                     "1-Tren gian Do", "2-Tren gian Xanh", "3-Tren gian Vang",
//                     "4-San Do",       "5-San Xanh",        "6-San Vang"
//                 };
//                 snprintf(buf, sizeof(buf), "%s: %s", names[i], lampSpinning[i]?"XOAY":"DUNG");
//                 for (int j = 0; buf[j]; j++) glutBitmapCharacter(GLUT_BITMAP_8_BY_13, buf[j]);
//             }

//         glPopMatrix();
//         glMatrixMode(GL_PROJECTION);
//     glPopMatrix();
//     glMatrixMode(GL_MODELVIEW);
//     glEnable(GL_LIGHTING);

//     glutSwapBuffers();
// }

// // ─── RESHAPE ──────────────────────────────────────────────────────
// void reshape(int w, int h) {
//     if (h == 0) h = 1;
//     glViewport(0, 0, w, h);
//     glMatrixMode(GL_PROJECTION);
//     glLoadIdentity();
//     gluPerspective(60.0, (double)w/h, 0.1, 100.0);
//     glMatrixMode(GL_MODELVIEW);
//     glLoadIdentity();
// }

// // ─── INIT ─────────────────────────────────────────────────────────
// void init() {
//     glClearColor(0.0f, 0.0f, 0.02f, 1.0f);
//     glEnable(GL_DEPTH_TEST);
//     glEnable(GL_LIGHTING);
//     glEnable(GL_NORMALIZE);
//     glShadeModel(GL_SMOOTH);
//     glEnable(GL_LIGHT0); glEnable(GL_LIGHT1); glEnable(GL_LIGHT2);
//     glEnable(GL_LIGHT3); glEnable(GL_LIGHT4); glEnable(GL_LIGHT5);
//     GLfloat zero[] = {0,0,0,1};
//     glLightModelfv(GL_LIGHT_MODEL_AMBIENT, zero);
// }

// int main(int argc, char** argv) {
//     glutInit(&argc, argv);
//     glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH);
//     glutInitWindowSize(1024, 768);
//     glutInitWindowPosition(100, 100);
//     glutCreateWindow("Cau 4 - Ban Phim: Bat/Tat Den & Dung Xoay");

//     init();

//     glutDisplayFunc(display);
//     glutReshapeFunc(reshape);
//     glutKeyboardFunc(keyboard);
//     glutIdleFunc(idle);

//     printf("=== CAU 4: TUONG TAC BAN PHIM (PHIEN BAN HOAN CHINH) ===\n");
//     printf("  R / r : Bat/tat den DO    (den 1 tren gian + den 4 san)\n");
//     printf("  G / g : Bat/tat den XANH  (den 2 tren gian + den 5 san)\n");
//     printf("  B / b : Bat/tat den VANG  (den 3 tren gian + den 6 san)\n");
//     printf("  1     : Dung/tiep tuc xoay den 1 (tren gian, Do)\n");
//     printf("  2     : Dung/tiep tuc xoay den 2 (tren gian, Xanh)\n");
//     printf("  3     : Dung/tiep tuc xoay den 3 (tren gian, Vang)\n");
//     printf("  4     : Dung/tiep tuc xoay den 4 (san, Do)\n");
//     printf("  5     : Dung/tiep tuc xoay den 5 (san, Xanh)\n");
//     printf("  6     : Dung/tiep tuc xoay den 6 (san, Vang)\n");
//     printf("  ESC   : Thoat\n");

//     glutMainLoop();
//     return 0;
// }