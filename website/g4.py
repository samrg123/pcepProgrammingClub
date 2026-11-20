import pygame
import moderngl
import numpy as np
import time

# --- SHADER CODE (GLSL) ---
# This is the actual "Engine". It runs on the GPU.
VERTEX_SHADER = """
#version 330
in vec2 in_vert;
void main() {
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330
uniform float iTime;
uniform vec2 iResolution;
uniform vec2 iMouse;

// Distance function for the "Hyper-Core"
float sdSphere(vec3 p, float s) { return length(p) - s; }
float sdTorus(vec3 p, vec2 t) {
    vec2 q = vec2(length(p.xz)-t.x, p.y);
    return length(q)-t.y;
}

// Smooth blending between shapes
float smin(float a, float b, float k) {
    float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    return mix(b, a, h) - k * h * (1.0 - h);
}

float map(vec3 p) {
    // Rotate the world over time
    float t = iTime * 0.3;
    mat2 rot = mat2(cos(t), sin(t), -sin(t), cos(t));
    p.xz *= rot;
    p.yz *= rot;

    // Create morphing geometric shapes
    float sphere = sdSphere(p, 1.0);
    float torus = sdTorus(p, vec2(1.2, 0.3));
    
    // The "glitch" effect based on mouse position
    float distortion = sin(p.x * 5.0 + iTime) * 0.1 * (iMouse.x / iResolution.x);
    
    // Blend shapes together organically
    float shape = smin(sphere, torus, 0.5);
    shape += distortion;
    
    // Carve out a fractal-like pattern
    shape -= sin(p.x * 10.0 + iTime) * 0.05;
    
    return shape;
}

vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.01, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;
    vec3 ro = vec3(0.0, 0.0, -4.0); // Camera position
    vec3 rd = normalize(vec3(uv, 1.2)); // Ray direction
    
    float t = 0.0;
    for(int i = 0; i < 80; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);
        if(d < 0.001 || t > 20.0) break;
        t += d;
    }
    
    vec3 color = vec3(0.0);
    if(t < 20.0) {
        vec3 p = ro + rd * t;
        vec3 n = calcNormal(p);
        vec3 lightDir = normalize(vec3(1.0, 1.0, -1.0));
        
        // Lighting calculations
        float diff = max(dot(n, lightDir), 0.0);
        float spec = pow(max(dot(reflect(-lightDir, n), -rd), 0.0), 32.0);
        
        // Cyberpunk Color Palette (Deep Purples and Cyans)
        vec3 baseColor = mix(vec3(0.1, 0.0, 0.3), vec3(0.0, 0.8, 1.0), n.y * 0.5 + 0.5);
        color = baseColor * diff + spec;
        
        // Neon Rim Lighting
        float rim = 1.0 - max(dot(n, -rd), 0.0);
        color += pow(rim, 4.0) * vec3(0.0, 1.0, 1.0) * 2.0;
    }
    
    // Background Gradient
    color += vec3(0.02, 0.01, 0.05) * (1.0 - length(uv));
    
    gl_FragColor = vec4(color, 1.0);
}
"""

class HyperCoreDemo:
    def __init__(self):
        pygame.init()
        self.screen_res = (1280, 720)
        pygame.display.set_mode(self.screen_res, pygame.OPENGL | pygame.DOUBLEBUF)
        pygame.display.set_caption("Hyper-Dimension Core | Move Mouse to Warp")
        
        # Initialize ModernGL
        self.ctx = moderngl.create_context()
        
        # Create a full-screen quad to render the shader onto
        self.quad_buffer = self.ctx.buffer(np.array([
            -1.0,  1.0,
            -1.0, -1.0,
             1.0,  1.0,
             1.0, -1.0,
        ], dtype='f4'))
        
        self.prog = self.ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)
        self.vao = self.ctx.vertex_array(self.prog, [(self.quad_buffer, '2f', 'in_vert')])
        
        self.start_time = time.time()
        self.clock = pygame.time.Clock()

    def run(self):
        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            # Update Uniforms
            current_time = time.time() - self.start_time
            mx, my = pygame.mouse.get_pos()
            
            self.prog['iTime'].value = current_time
            self.prog['iResolution'].value = self.screen_res
            self.prog['iMouse'].value = (mx, my)
            
            # Render
            self.ctx.clear(0, 0, 0)
            self.vao.render(moderngl.TRIANGLE_STRIP)
            
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

if __name__ == "__main__":
    demo = HyperCoreDemo()
    demo.run()
