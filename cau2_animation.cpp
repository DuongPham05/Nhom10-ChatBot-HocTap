// /*
// =============================================================
//   CÂU 2 (3 điểm): VẼ VÀ CÀI ĐẶT CHUYỂN ĐỘNG CHO ĐÈN PHA
// =============================================================
//   KHÔNG dùng hàm vẽ khối 3D dựng sẵn (không dùng glutSolidSphere,
//   glutSolidCone, glutSolidCylinder, v.v.). Tất cả vẽ thủ công.

//   Yêu cầu:
//   2.1 (1đ): Thanh ngang treo đèn pha di chuyển lên xuống liên tục
//             theo trục Y theo thời gian (dao động sin)
//   2.2 (1đ): Cả 3 đèn pha trên giàn di chuyển lên xuống CÙNG thanh ngang
//   2.3 (1đ): Cả 6 đèn pha (3 trên giàn + 3 sàn) tự động xoay liên tục
//             quanh trục Y của chính mỗi đèn

//   COMPILE:
//     Windows: g++ cau2_animation.cpp -o cau2 -lfreeglut -lopengl32 -lglu32
//     Linux:   g++ cau2_animation.cpp -o cau2 -lGL -lGLU -lglut
//     macOS:   g++ cau2_animation.cpp -o cau2 -framework OpenGL -framework GLUT
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

// // ─── BIẾN ANIMATION ─────────────────────────────────────────────
// float gTime      = 0.0f;   // Thời gian tích lũy
// float trussY     = 4.0f;   // Y hiện tại của giàn đèn (dao động)

// // Góc xoay của 6 đèn (0-2: trên giàn, 3-5: sàn)
// float lampAngle[6] = {0, 0, 0, 0, 0, 0};

// // ─── VẼ KHỐI HỘP THỦ CÔNG ───────────────────────────────────────
// void drawBox(float w, float h, float d) {
//     float hw = w * 0.5f, hh = h * 0.5f, hd = d * 0.5f;
//     glBegin(GL_QUADS);
//         glNormal3f(0, 0, 1);
//         glVertex3f(-hw,-hh, hd); glVertex3f( hw,-hh, hd);
//         glVertex3f( hw, hh, hd); glVertex3f(-hw, hh, hd);

//         glNormal3f(0, 0,-1);
//         glVertex3f( hw,-hh,-hd); glVertex3f(-hw,-hh,-hd);
//         glVertex3f(-hw, hh,-hd); glVertex3f( hw, hh,-hd);

//         glNormal3f(-1, 0, 0);
//         glVertex3f(-hw,-hh,-hd); glVertex3f(-hw,-hh, hd);
//         glVertex3f(-hw, hh, hd); glVertex3f(-hw, hh,-hd);

//         glNormal3f(1, 0, 0);
//         glVertex3f( hw,-hh, hd); glVertex3f( hw,-hh,-hd);
//         glVertex3f( hw, hh,-hd); glVertex3f( hw, hh, hd);

//         glNormal3f(0, 1, 0);
//         glVertex3f(-hw, hh, hd); glVertex3f( hw, hh, hd);
//         glVertex3f( hw, hh,-hd); glVertex3f(-hw, hh,-hd);

//         glNormal3f(0,-1, 0);
//         glVertex3f(-hw,-hh,-hd); glVertex3f( hw,-hh,-hd);
//         glVertex3f( hw,-hh, hd); glVertex3f(-hw,-hh, hd);
//     glEnd();
// }

// // ─── VẼ KHỐI TRỤ THỦ CÔNG ───────────────────────────────────────
// void drawCylinder(float radius, float height, int slices) {
//     float step = 2.0f * PI / slices;
//     glBegin(GL_QUAD_STRIP);
//     for (int i = 0; i <= slices; i++) {
//         float a = i * step;
//         float nx = cosf(a), nz = sinf(a);
//         glNormal3f(nx, 0, nz);
//         glVertex3f(radius * nx, 0,      radius * nz);
//         glVertex3f(radius * nx, height, radius * nz);
//     }
//     glEnd();
//     glBegin(GL_TRIANGLE_FAN);
//     glNormal3f(0, 1, 0);
//     glVertex3f(0, height, 0);
//     for (int i = 0; i <= slices; i++) {
//         float a = i * step;
//         glVertex3f(radius * cosf(a), height, radius * sinf(a));
//     }
//     glEnd();
//     glBegin(GL_TRIANGLE_FAN);
//     glNormal3f(0, -1, 0);
//     glVertex3f(0, 0, 0);
//     for (int i = slices; i >= 0; i--) {
//         float a = i * step;
//         glVertex3f(radius * cosf(a), 0, radius * sinf(a));
//     }
//     glEnd();
// }

// // ─── VẼ HÌNH NÓN THỦ CÔNG (chụp đèn) ───────────────────────────
// //   baseR: bán kính đáy, topR: bán kính đỉnh, height: chiều cao
// //   Trục Y âm (nón nhọn hướng xuống từ gốc)
// void drawCone(float baseR, float topR, float height, int slices) {
//     float step = 2.0f * PI / slices;
//     glBegin(GL_QUAD_STRIP);
//     for (int i = 0; i <= slices; i++) {
//         float a = i * step;
//         float c = cosf(a), s = sinf(a);
//         glNormal3f(c, 0.3f, s);
//         glVertex3f(topR  * c,       0, topR  * s);
//         glVertex3f(baseR * c, -height, baseR * s);
//     }
//     glEnd();
// }

// // ─── MẶT SÀN ─────────────────────────────────────────────────────
// void drawStageFloor() {
//     GLfloat mat_amb[] = {0.05f, 0.05f, 0.05f, 1.0f};
//     GLfloat mat_dif[] = {0.15f, 0.15f, 0.15f, 1.0f};
//     glMaterialfv(GL_FRONT, GL_AMBIENT, mat_amb);
//     glMaterialfv(GL_FRONT, GL_DIFFUSE, mat_dif);

//     glNormal3f(0, 1, 0);
//     glBegin(GL_QUADS);
//         glVertex3f(-6.0f, 0.0f, -5.0f);
//         glVertex3f( 6.0f, 0.0f, -5.0f);
//         glVertex3f( 6.0f, 0.0f,  5.0f);
//         glVertex3f(-6.0f, 0.0f,  5.0f);
//     glEnd();

//     // Grid
//     glDisable(GL_LIGHTING);
//     glColor3f(0.2f, 0.2f, 0.2f);
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

// // ─── GIÀN ĐÈN (TRUSS) ────────────────────────────────────────────
// //   Vị trí Y thay đổi theo trussY (Câu 2.1 + 2.2)
// void drawTruss() {
//     GLfloat mat_amb[] = {0.2f, 0.2f, 0.2f, 1.0f};
//     GLfloat mat_dif[] = {0.5f, 0.5f, 0.5f, 1.0f};
//     GLfloat mat_spe[] = {0.8f, 0.8f, 0.8f, 1.0f};
//     GLfloat mat_shi[] = {80.0f};
//     glMaterialfv(GL_FRONT, GL_AMBIENT,   mat_amb);
//     glMaterialfv(GL_FRONT, GL_DIFFUSE,   mat_dif);
//     glMaterialfv(GL_FRONT, GL_SPECULAR,  mat_spe);
//     glMaterialfv(GL_FRONT, GL_SHININESS, mat_shi);

//     // Cột trái: X=-4.5, từ Y=0 đến Y=trussY
//     glPushMatrix();
//         glTranslatef(-4.5f, 0.0f, 0.0f);
//         drawCylinder(0.12f, trussY, 12);
//     glPopMatrix();

//     // Cột phải: X=+4.5, từ Y=0 đến Y=trussY
//     glPushMatrix();
//         glTranslatef(4.5f, 0.0f, 0.0f);
//         drawCylinder(0.12f, trussY, 12);
//     glPopMatrix();

//     // Thanh ngang tại Y=trussY (Câu 2.1: di chuyển lên xuống)
//     glPushMatrix();
//         glTranslatef(0.0f, trussY, 0.0f);
//         drawBox(9.2f, 0.2f, 0.2f);
//     glPopMatrix();
// }

// // ─── ĐÈN PHA TRÊN GIÀN (chiếu xuống) ────────────────────────────
// //   Câu 2.2: đèn di chuyển lên xuống CÙNG thanh ngang (dùng trussY)
// //   Câu 2.3: đèn xoay quanh trục Y của chính nó (dùng lampAngle)
// void drawTrussSpotlight(float offsetX, int lampIdx) {
//     // Màu theo đèn
//     float colors[3][3] = {
//         {1.0f, 0.0f, 0.0f},   // Đèn 0: Đỏ
//         {0.0f, 0.4f, 1.0f},   // Đèn 1: Xanh dương
//         {1.0f, 1.0f, 0.0f},   // Đèn 2: Vàng
//     };
//     float r = colors[lampIdx][0];
//     float g = colors[lampIdx][1];
//     float b = colors[lampIdx][2];

//     // Câu 2.2: đặt tại Y = trussY - 0.15 (treo dưới thanh ngang, cùng trussY)
//     glPushMatrix();
//         glTranslatef(offsetX, trussY - 0.15f, 0.0f);

//         // Câu 2.3: xoay quanh trục Y của chính đèn
//         glRotatef(lampAngle[lampIdx], 0.0f, 1.0f, 0.0f);

//         // Thân đèn - hộp xám kim loại
//         GLfloat body_amb[] = {0.3f, 0.3f, 0.3f, 1.0f};
//         GLfloat body_dif[] = {0.6f, 0.6f, 0.6f, 1.0f};
//         GLfloat body_spe[] = {1.0f, 1.0f, 1.0f, 1.0f};
//         GLfloat body_shi[] = {100.0f};
//         glMaterialfv(GL_FRONT, GL_AMBIENT,   body_amb);
//         glMaterialfv(GL_FRONT, GL_DIFFUSE,   body_dif);
//         glMaterialfv(GL_FRONT, GL_SPECULAR,  body_spe);
//         glMaterialfv(GL_FRONT, GL_SHININESS, body_shi);
//         drawBox(0.3f, 0.3f, 0.3f);

//         // Chụp đèn hình nón chiếu xuống - có màu phát sáng
//         GLfloat em[]       = {r * 0.8f, g * 0.8f, b * 0.8f, 1.0f};
//         GLfloat cone_dif[] = {r, g, b, 0.4f};
//         glMaterialfv(GL_FRONT, GL_EMISSION, em);
//         glMaterialfv(GL_FRONT, GL_DIFFUSE,  cone_dif);
//         glEnable(GL_BLEND);
//         glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

//         glPushMatrix();
//             glTranslatef(0.0f, -0.15f, 0.0f);
//             drawCone(0.8f, 0.15f, 1.8f, 16);
//         glPopMatrix();

//         glDisable(GL_BLEND);
//         GLfloat zero_em[] = {0, 0, 0, 1};
//         glMaterialfv(GL_FRONT, GL_EMISSION, zero_em);
//     glPopMatrix();
// }

// // ─── ĐÈN PHA SÀN (chiếu lên) ─────────────────────────────────────
// //   Câu 2.3: xoay quanh trục Y của chính đèn
// void drawFloorSpotlight(float posX, float posZ, int lampIdx) {
//     float colors[3][3] = {
//         {1.0f, 0.0f, 0.0f},
//         {0.0f, 0.4f, 1.0f},
//         {1.0f, 1.0f, 0.0f},
//     };
//     // lampIdx 3,4,5 → colorIdx 0,1,2
//     int ci = lampIdx - 3;
//     float r = colors[ci][0];
//     float g = colors[ci][1];
//     float b = colors[ci][2];

//     glPushMatrix();
//         glTranslatef(posX, 0.0f, posZ);

//         // Câu 2.3: xoay quanh trục Y của chính đèn
//         glRotatef(lampAngle[lampIdx], 0.0f, 1.0f, 0.0f);

//         // Thân đèn sàn
//         GLfloat body_amb[] = {0.3f, 0.3f, 0.3f, 1.0f};
//         GLfloat body_dif[] = {0.6f, 0.6f, 0.6f, 1.0f};
//         glMaterialfv(GL_FRONT, GL_AMBIENT, body_amb);
//         glMaterialfv(GL_FRONT, GL_DIFFUSE, body_dif);
//         drawBox(0.25f, 0.25f, 0.25f);

//         // Nón chiếu lên (Y+): quay 180° quanh X để nón hướng lên
//         GLfloat em[]       = {r * 0.8f, g * 0.8f, b * 0.8f, 1.0f};
//         GLfloat cone_dif[] = {r, g, b, 0.35f};
//         glMaterialfv(GL_FRONT, GL_EMISSION, em);
//         glMaterialfv(GL_FRONT, GL_DIFFUSE,  cone_dif);
//         glEnable(GL_BLEND);
//         glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

//         glPushMatrix();
//             glTranslatef(0.0f, 0.125f, 0.0f);
//             glRotatef(180.0f, 1.0f, 0.0f, 0.0f);  // Lật nón hướng lên
//             drawCone(1.5f, 0.15f, 3.5f, 16);
//         glPopMatrix();

//         glDisable(GL_BLEND);
//         GLfloat zero_em[] = {0, 0, 0, 1};
//         glMaterialfv(GL_FRONT, GL_EMISSION, zero_em);
//     glPopMatrix();
// }

// // ─── IDLE: CẬP NHẬT ANIMATION ────────────────────────────────────
// void idle() {
//     const float dt = 0.016f;  // ~60 FPS
//     gTime += dt;

//     // Câu 2.1 + 2.2: Thanh ngang (và 3 đèn trên giàn) di chuyển lên xuống
//     // Dao động sin: trussY ∈ [3.0, 5.0], tần số = 0.8 rad/s
//     trussY = 4.0f + sinf(gTime * 0.8f) * 1.0f;

//     // Câu 2.3: Cả 6 đèn xoay quanh trục Y của chính mình
//     for (int i = 0; i < 6; i++) {
//         // Đèn trên giàn (0,1,2): 60 độ/giây
//         // Đèn sàn (3,4,5):       45 độ/giây
//         float speed = (i < 3) ? 60.0f : 45.0f;
//         lampAngle[i] += speed * dt;
//         if (lampAngle[i] >= 360.0f) lampAngle[i] -= 360.0f;
//     }

//     glutPostRedisplay();
// }

// // ─── DISPLAY ─────────────────────────────────────────────────────
// void display() {
//     glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
//     glLoadIdentity();

//     // Camera Flycam
//     gluLookAt(0.0, 8.0, 12.0,
//               0.0, 2.0,  0.0,
//               0.0, 1.0,  0.0);

//     // Ánh sáng nhẹ để thấy cảnh (phần ánh sáng Spotlight đầy đủ ở Câu 3)
//     GLfloat lpos[] = {0.0f, 10.0f, 8.0f, 1.0f};
//     GLfloat ldif[] = {0.4f, 0.4f, 0.4f, 1.0f};
//     glLightfv(GL_LIGHT0, GL_POSITION, lpos);
//     glLightfv(GL_LIGHT0, GL_DIFFUSE,  ldif);
//     glEnable(GL_LIGHT0);

//     // Sàn
//     drawStageFloor();

//     // Câu 2.1 + 2.2: Giàn đèn di chuyển lên xuống
//     drawTruss();

//     // Câu 2.2: 3 đèn trên giàn di chuyển cùng trussY
//     // Câu 2.3: mỗi đèn xoay theo lampAngle của nó
//     drawTrussSpotlight(-3.0f, 0);  // Đèn đỏ
//     drawTrussSpotlight( 0.0f, 1);  // Đèn xanh
//     drawTrussSpotlight( 3.0f, 2);  // Đèn vàng

//     // Câu 2.3: 3 đèn sàn xoay
//     drawFloorSpotlight(-3.0f, 4.5f, 3);
//     drawFloorSpotlight( 0.0f, 4.5f, 4);
//     drawFloorSpotlight( 3.0f, 4.5f, 5);

//     glutSwapBuffers();
// }

// // ─── RESHAPE ─────────────────────────────────────────────────────
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
//     glEnable(GL_COLOR_MATERIAL);
//     glShadeModel(GL_SMOOTH);
//     GLfloat global_amb[] = {0.05f, 0.05f, 0.05f, 1.0f};
//     glLightModelfv(GL_LIGHT_MODEL_AMBIENT, global_amb);
// }

// int main(int argc, char** argv) {
//     glutInit(&argc, argv);
//     glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH);
//     glutInitWindowSize(1024, 768);
//     glutInitWindowPosition(100, 100);
//     glutCreateWindow("Cau 2 - Animation: Truss Up/Down & Den Xoay");

//     init();

//     glutDisplayFunc(display);
//     glutReshapeFunc(reshape);
//     glutKeyboardFunc(keyboard);
//     glutIdleFunc(idle);

//     printf("=== CAU 2: CHUYEN DONG DEN PHA ===\n");
//     printf("2.1 + 2.2: Thanh ngang (va 3 den tren gian) len xuong theo sin\n");
//     printf("2.3: Ca 6 den xoay quanh truc Y cua chinh minh\n");
//     printf("     Den tren gian: 60 do/giay\n");
//     printf("     Den san:       45 do/giay\n");
//     printf("ESC: Thoat\n");

//     glutMainLoop();
//     return 0;
// }
