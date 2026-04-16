// /*
// =============================================================
//   CÂU 1 (2 điểm): THIẾT LẬP HỆ TỌA ĐỘ 3D & CẢNH CƠ BẢN
// =============================================================
//   Yêu cầu:
//   - Thiết lập hệ tọa độ 3D (Perspective)
//   - Tạo mặt phẳng (Plane/Grid) làm mặt sàn sân khấu
//   - Vẽ hệ thống giàn đèn treo ở phía trên (trụ đứng + thanh ngang)
//   - Đặt Camera ở vị trí FLYCAM trên cao, bao quát toàn bộ sân khấu

//   COMPILE:
//     Windows: g++ cau1_setup_scene.cpp -o cau1 -lfreeglut -lopengl32 -lglu32
//     Linux:   g++ cau1_setup_scene.cpp -o cau1 -lGL -lGLU -lglut
//     macOS:   g++ cau1_setup_scene.cpp -o cau1 -framework OpenGL -framework GLUT
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

// // ─── Chiều cao cố định của giàn đèn (Câu 1 chưa có animation) ───
// const float TRUSS_Y = 4.0f;

// // ─── VẼ KHỐI HỘP THỦ CÔNG (không dùng glutSolidCube) ───────────
// void drawBox(float w, float h, float d) {
//     float hw = w * 0.5f, hh = h * 0.5f, hd = d * 0.5f;
//     glBegin(GL_QUADS);
//         // Mặt trước (Z+)
//         glNormal3f(0, 0, 1);
//         glVertex3f(-hw, -hh,  hd); glVertex3f( hw, -hh,  hd);
//         glVertex3f( hw,  hh,  hd); glVertex3f(-hw,  hh,  hd);
//         // Mặt sau (Z-)
//         glNormal3f(0, 0, -1);
//         glVertex3f( hw, -hh, -hd); glVertex3f(-hw, -hh, -hd);
//         glVertex3f(-hw,  hh, -hd); glVertex3f( hw,  hh, -hd);
//         // Mặt trái (X-)
//         glNormal3f(-1, 0, 0);
//         glVertex3f(-hw, -hh, -hd); glVertex3f(-hw, -hh,  hd);
//         glVertex3f(-hw,  hh,  hd); glVertex3f(-hw,  hh, -hd);
//         // Mặt phải (X+)
//         glNormal3f(1, 0, 0);
//         glVertex3f( hw, -hh,  hd); glVertex3f( hw, -hh, -hd);
//         glVertex3f( hw,  hh, -hd); glVertex3f( hw,  hh,  hd);
//         // Mặt trên (Y+)
//         glNormal3f(0, 1, 0);
//         glVertex3f(-hw,  hh,  hd); glVertex3f( hw,  hh,  hd);
//         glVertex3f( hw,  hh, -hd); glVertex3f(-hw,  hh, -hd);
//         // Mặt dưới (Y-)
//         glNormal3f(0, -1, 0);
//         glVertex3f(-hw, -hh, -hd); glVertex3f( hw, -hh, -hd);
//         glVertex3f( hw, -hh,  hd); glVertex3f(-hw, -hh,  hd);
//     glEnd();
// }

// // ─── VẼ KHỐI TRỤ THỦ CÔNG (không dùng hàm dựng sẵn) ────────────
// void drawCylinder(float radius, float height, int slices) {
//     float step = 2.0f * PI / slices;
//     // Thân trụ
//     glBegin(GL_QUAD_STRIP);
//     for (int i = 0; i <= slices; i++) {
//         float angle = i * step;
//         float nx = cosf(angle), nz = sinf(angle);
//         glNormal3f(nx, 0, nz);
//         glVertex3f(radius * nx, 0,      radius * nz);
//         glVertex3f(radius * nx, height, radius * nz);
//     }
//     glEnd();
//     // Đáy trên
//     glBegin(GL_TRIANGLE_FAN);
//     glNormal3f(0, 1, 0);
//     glVertex3f(0, height, 0);
//     for (int i = 0; i <= slices; i++) {
//         float a = i * step;
//         glVertex3f(radius * cosf(a), height, radius * sinf(a));
//     }
//     glEnd();
//     // Đáy dưới
//     glBegin(GL_TRIANGLE_FAN);
//     glNormal3f(0, -1, 0);
//     glVertex3f(0, 0, 0);
//     for (int i = slices; i >= 0; i--) {
//         float a = i * step;
//         glVertex3f(radius * cosf(a), 0, radius * sinf(a));
//     }
//     glEnd();
// }

// // ─── MẶT SÀN SÂN KHẤU (Y=0, X∈[-6,6], Z∈[-5,5]) ───────────────
// void drawStageFloor() {
//     // Vật liệu sàn tối (cảnh ban đêm)
//     GLfloat mat_amb[] = {0.05f, 0.05f, 0.05f, 1.0f};
//     GLfloat mat_dif[] = {0.15f, 0.15f, 0.15f, 1.0f};
//     GLfloat mat_spe[] = {0.4f,  0.4f,  0.4f,  1.0f};
//     GLfloat mat_shi[] = {60.0f};
//     glMaterialfv(GL_FRONT, GL_AMBIENT,   mat_amb);
//     glMaterialfv(GL_FRONT, GL_DIFFUSE,   mat_dif);
//     glMaterialfv(GL_FRONT, GL_SPECULAR,  mat_spe);
//     glMaterialfv(GL_FRONT, GL_SHININESS, mat_shi);

//     // Mặt sàn chính
//     glNormal3f(0, 1, 0);
//     glBegin(GL_QUADS);
//         glVertex3f(-6.0f, 0.0f, -5.0f);
//         glVertex3f( 6.0f, 0.0f, -5.0f);
//         glVertex3f( 6.0f, 0.0f,  5.0f);
//         glVertex3f(-6.0f, 0.0f,  5.0f);
//     glEnd();

//     // Lưới kẻ (Grid) để thấy rõ mặt sàn
//     glDisable(GL_LIGHTING);
//     glColor3f(0.25f, 0.25f, 0.25f);
//     glLineWidth(1.0f);
//     glBegin(GL_LINES);
//     // Đường dọc (song song Z)
//     for (int x = -6; x <= 6; x++) {
//         glVertex3f((float)x, 0.01f, -5.0f);
//         glVertex3f((float)x, 0.01f,  5.0f);
//     }
//     // Đường ngang (song song X)
//     for (int z = -5; z <= 5; z++) {
//         glVertex3f(-6.0f, 0.01f, (float)z);
//         glVertex3f( 6.0f, 0.01f, (float)z);
//     }
//     glEnd();
//     glEnable(GL_LIGHTING);
// }

// // ─── GIÀN ĐÈN (TRUSS SYSTEM) ────────────────────────────────────
// //   Gồm: 2 cột trụ đứng (X=-4.5 và X=+4.5) + 1 thanh ngang nối
// //   Ở Câu 1 giàn cố định tại Y = TRUSS_Y
// void drawTruss(float trussY) {
//     GLfloat mat_amb[] = {0.2f, 0.2f, 0.2f, 1.0f};
//     GLfloat mat_dif[] = {0.5f, 0.5f, 0.5f, 1.0f};
//     GLfloat mat_spe[] = {0.8f, 0.8f, 0.8f, 1.0f};
//     GLfloat mat_shi[] = {80.0f};
//     glMaterialfv(GL_FRONT, GL_AMBIENT,   mat_amb);
//     glMaterialfv(GL_FRONT, GL_DIFFUSE,   mat_dif);
//     glMaterialfv(GL_FRONT, GL_SPECULAR,  mat_spe);
//     glMaterialfv(GL_FRONT, GL_SHININESS, mat_shi);

//     // Cột trụ đứng trái tại X = -4.5, từ Y=0 đến Y=trussY
//     glPushMatrix();
//         glTranslatef(-4.5f, 0.0f, 0.0f);
//         drawCylinder(0.12f, trussY, 12);
//     glPopMatrix();

//     // Cột trụ đứng phải tại X = +4.5, từ Y=0 đến Y=trussY
//     glPushMatrix();
//         glTranslatef(4.5f, 0.0f, 0.0f);
//         drawCylinder(0.12f, trussY, 12);
//     glPopMatrix();

//     // Thanh ngang nằm ngang tại Y = trussY
//     // Vẽ bằng drawBox: rộng 9.2 (từ -4.6 đến +4.6), cao 0.2, sâu 0.2
//     glPushMatrix();
//         glTranslatef(0.0f, trussY, 0.0f);
//         drawBox(9.2f, 0.2f, 0.2f);
//     glPopMatrix();
// }

// // ─── ĐÈN PHA ĐƠN GIẢN (Câu 1: chỉ vẽ hình, chưa có ánh sáng thực) ──
// void drawSimpleSpotlight(float offsetX, float trussY) {
//     GLfloat mat_amb[] = {0.3f, 0.3f, 0.3f, 1.0f};
//     GLfloat mat_dif[] = {0.6f, 0.6f, 0.6f, 1.0f};
//     glMaterialfv(GL_FRONT, GL_AMBIENT, mat_amb);
//     glMaterialfv(GL_FRONT, GL_DIFFUSE, mat_dif);

//     glPushMatrix();
//         glTranslatef(offsetX, trussY - 0.15f, 0.0f);
//         drawBox(0.3f, 0.3f, 0.3f);
//     glPopMatrix();
// }

// // ─── HÀM DISPLAY ────────────────────────────────────────────────
// void display() {
//     glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
//     glLoadIdentity();

//     // ── CAMERA: FLYCAM - trên cao nhìn xuống toàn bộ sân khấu ──
//     //   Eye    (0, 8, 12): phía trên và phía trước sân khấu
//     //   Center (0, 2,  0): nhìn vào giữa sân khấu
//     //   Up     (0, 1,  0): hướng lên là trục Y
//     gluLookAt(0.0, 8.0, 12.0,
//               0.0, 2.0,  0.0,
//               0.0, 1.0,  0.0);

//     // Thiết lập ánh sáng môi trường tối thiểu để thấy hình dạng
//     GLfloat light0_pos[] = {0.0f, 10.0f, 5.0f, 1.0f};
//     GLfloat light0_dif[] = {0.6f, 0.6f, 0.6f, 1.0f};
//     glLightfv(GL_LIGHT0, GL_POSITION, light0_dif);
//     glLightfv(GL_LIGHT0, GL_DIFFUSE,  light0_dif);
//     glLightfv(GL_LIGHT0, GL_POSITION, light0_pos);
//     glEnable(GL_LIGHT0);

//     // ── VẼ SÀN SÂN KHẤU ──
//     drawStageFloor();

//     // ── VẼ GIÀN ĐÈN (TRUSS) cố định tại Y = TRUSS_Y ──
//     drawTruss(TRUSS_Y);

//     // ── VẼ 3 ĐÈN PHA TRÊN GIÀN (hình dạng đơn giản) ──
//     //   Đèn tại X=-3, X=0, X=+3
//     drawSimpleSpotlight(-3.0f, TRUSS_Y);
//     drawSimpleSpotlight( 0.0f, TRUSS_Y);
//     drawSimpleSpotlight( 3.0f, TRUSS_Y);

//     glutSwapBuffers();
// }

// // ─── RESHAPE: Thiết lập Perspective 3D ──────────────────────────
// void reshape(int w, int h) {
//     if (h == 0) h = 1;
//     glViewport(0, 0, w, h);

//     glMatrixMode(GL_PROJECTION);
//     glLoadIdentity();
//     // Perspective: FOV=60°, aspect=w/h, near=0.1, far=100
//     gluPerspective(60.0, (double)w / h, 0.1, 100.0);

//     glMatrixMode(GL_MODELVIEW);
//     glLoadIdentity();
// }

// // ─── INIT ────────────────────────────────────────────────────────
// void init() {
//     glClearColor(0.0f, 0.0f, 0.02f, 1.0f);  // Nền đen (ban đêm)
//     glEnable(GL_DEPTH_TEST);
//     glEnable(GL_LIGHTING);
//     glEnable(GL_NORMALIZE);
//     glShadeModel(GL_SMOOTH);

//     // Ambient nhẹ để thấy cảnh
//     GLfloat global_ambient[] = {0.1f, 0.1f, 0.1f, 1.0f};
//     glLightModelfv(GL_LIGHT_MODEL_AMBIENT, global_ambient);
// }

// void keyboard(unsigned char key, int x, int y) {
//     if (key == 27) exit(0);  // ESC thoát
// }

// int main(int argc, char** argv) {
//     glutInit(&argc, argv);
//     glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH);
//     glutInitWindowSize(1024, 768);
//     glutInitWindowPosition(100, 100);
//     glutCreateWindow("Cau 1 - San Khau Ca Nhac: Setup Scene & Camera");

//     init();

//     glutDisplayFunc(display);
//     glutReshapeFunc(reshape);
//     glutKeyboardFunc(keyboard);

//     printf("=== CAU 1: THIET LAP HE TOA DO 3D & CANH CO BAN ===\n");
//     printf("Camera FLYCAM tai (0, 8, 12) nhin vao (0, 2, 0)\n");
//     printf("San khau: Y=0, X=[-6,6], Z=[-5,5]\n");
//     printf("Gian den (Truss): Y=%.1f co dinh\n", TRUSS_Y);
//     printf("ESC: Thoat\n");

//     glutMainLoop();
//     return 0;
// }
