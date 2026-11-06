; Memory Barriers / synchronization
0:  89 84 24 00 80 ff ff    mov    DWORD PTR [rsp-0x8000],eax
7:  55                      push   rbp
8:  48 83 ec 50             sub    rsp,0x50
c:  41 81 7f 20 01 00 00    cmp    DWORD PTR [r15+0x20],0x1
13: 00 
14: 74 05                   je     0x1b
16: e8 c5 a5 22 07          call   0x722a5e0
1b: 48 b9 28 85 ac 6c c3    movabs rcx,0x2c36cac8528
22: 02 00 00 
25: 8b b1 90 00 00 00       mov    esi,DWORD PTR [rcx+0x90]
2b: 83 c6 02                add    esi,0x2
2e: 89 b1 90 00 00 00       mov    DWORD PTR [rcx+0x90],esi
34: 81 e6 fe 07 00 00       and    esi,0x7fe
3a: 85 f6                   test   esi,esi
3c: 0f 84 f9 00 00 00       je     0x13b

; Start of our code
42: be 00 00 00 00          mov    esi,0x0
47: e9 4c 00 00 00          jmp    0x98
4c: 0f 1f 40 00             nop    DWORD PTR [rax+0x0]

; LoopBody
50: ff c0                   inc    eax
52: 48 33 c2                xor    rax,rdx
55: ff c6                   inc    esi
57: 48 bf 28 85 ac 6c c3    movabs rdi,0x2c36cac8528
5e: 02 00 00 
61: 8b 9f 94 00 00 00       mov    ebx,DWORD PTR [rdi+0x94]
67: 83 c3 02                add    ebx,0x2
6a: 89 9f 94 00 00 00       mov    DWORD PTR [rdi+0x94],ebx
70: 81 e3 fe 3f 00 00       and    ebx,0x3ffe
76: 85 db                   test   ebx,ebx
78: 0f 84 de 00 00 00       je     0x15c

; loop test
7e: 4d 8b 57 30             mov    r10,QWORD PTR [r15+0x30]
82: 41 85 02                test   DWORD PTR [r10],eax
85: 48 bf 28 85 ac 6c c3    movabs rdi,0x2c36cac8528
8c: 02 00 00 
8f: ff 87 f8 00 00 00       inc    DWORD PTR [rdi+0xf8]
95: 48 8b d0                mov    rdx,rax
98: 81 fe 00 ca 9a 3b       cmp    esi,0x3b9aca00
9e: 48 b8 28 85 ac 6c c3    movabs rax,0x2c36cac8528
a5: 02 00 00 
a8: bf e8 00 00 00          mov    edi,0xe8
ad: 7c 05                   jl     0xb4
af: bf d8 00 00 00          mov    edi,0xd8
b4: 48 8b 1c 38             mov    rbx,QWORD PTR [rax+rdi*1]
b8: 48 8d 5b 01             lea    rbx,[rbx+0x1]
bc: 48 89 1c 38             mov    QWORD PTR [rax+rdi*1],rbx
c0: 48 8b c2                mov    rax,rdx
c3: 7c 8b                   jl     0

; function return
c5: 48 83 c4 50             add    rsp,0x50
c9: 5d                      pop    rbp
ca: 49 3b 67 28             cmp    rsp,QWORD PTR [r15+0x28]
ce: 0f 87 a9 00 00 00       ja     0x17d
d4: c3                      ret

; Exception handling
d5: 89 84 24 00 80 ff ff    mov    DWORD PTR [rsp-0x8000],eax
dc: 55                      push   rbp
dd: 48 83 ec 50             sub    rsp,0x50
e1: 66 66 90                data16 xchg ax,ax
e4: 41 81 7f 20 00 00 00    cmp    DWORD PTR [r15+0x20],0x0
eb: 00 
ec: 74 05                   je     0xf3
ee: e8 ed a4 22 07          call   0x722a5e0
f3: b9 08 00 00 00          mov    ecx,0x8
f8: 48 63 c9                movsxd rcx,ecx
fb: 8b 34 0a                mov    esi,DWORD PTR [rdx+rcx*1]
fe: b9 00 00 00 00          mov    ecx,0x0
103:    48 63 c9                movsxd rcx,ecx
106:    8b 3c 0a                mov    edi,DWORD PTR [rdx+rcx*1]
109:    48 8b ca                mov    rcx,rdx
10c:    89 74 24 44             mov    DWORD PTR [rsp+0x44],esi
110:    89 7c 24 40             mov    DWORD PTR [rsp+0x40],edi
114:    48 b8 c0 9b 1d 6f f8    movabs rax,0x7ff86f1d9bc0
11b:    7f 00 00 
11e:    ff d0                   call   rax
120:    0f 1f 84 00 00 00 00    nop    DWORD PTR [rax+rax*1+0x0]
127:    00 
128:    8b 7c 24 40             mov    edi,DWORD PTR [rsp+0x40]
12c:    48 8b f7                mov    rsi,rdi
12f:    8b 44 24 44             mov    eax,DWORD PTR [rsp+0x44]
133:    48 8b d0                mov    rdx,rax
136:    e9 5d ff ff ff          jmp    0x98
13b:    49 ba c8 82 ac 6c c3    movabs r10,0x2c36cac82c8
142:    02 00 00 
145:    4c 89 54 24 08          mov    QWORD PTR [rsp+0x8],r10
14a:    48 c7 04 24 ff ff ff    mov    QWORD PTR [rsp],0xffffffffffffffff
151:    ff 
152:    e8 89 13 32 07          call   0x73214e0
157:    e9 e6 fe ff ff          jmp    0x42
15c:    49 ba c8 82 ac 6c c3    movabs r10,0x2c36cac82c8
163:    02 00 00 
166:    4c 89 54 24 08          mov    QWORD PTR [rsp+0x8],r10
16b:    48 c7 04 24 11 00 00    mov    QWORD PTR [rsp],0x11
172:    00 
173:    e8 68 13 32 07          call   0x73214e0
178:    e9 01 ff ff ff          jmp    0x7e
17d:    49 ba ca c0 cf 4f c3    movabs r10,0x2c34fcfc0ca
184:    02 00 00 
187:    4d 89 97 e0 04 00 00    mov    QWORD PTR [r15+0x4e0],r10
18e:    e9 cd 60 24 07          jmp    0x7246260
193:    49 8b 87 88 05 00 00    mov    rax,QWORD PTR [r15+0x588]
19a:    49 c7 87 88 05 00 00    mov    QWORD PTR [r15+0x588],0x0
1a1:    00 00 00 00 
1a5:    49 c7 87 90 05 00 00    mov    QWORD PTR [r15+0x590],0x0
1ac:    00 00 00 00 
1b0:    48 83 c4 50             add    rsp,0x50
1b4:    5d                      pop    rbp
1b5:    e9 a6 92 31 07          jmp    0x7319460
1ba:    f4                      hlt
1bb:    f4                      hlt
1bc:    f4                      hlt
1bd:    f4                      hlt
1be:    f4                      hlt
1bf:    f4                      hlt
1c0:    e8 9b c8 31 07          call   0x731ca60
1c5:    48 b9 38 08 85 6f f8    movabs rcx,0x7ff86f850838
1cc:    7f 00 00 
1cf:    48 83 e4 f0             and    rsp,0xfffffffffffffff0
1d3:    48 b8 50 8c 48 6f f8    movabs rax,0x7ff86f488c50
1da:    7f 00 00 
1dd:    ff d0                   call   rax
1df:    f4                      hlt
1e0:    49 ba e0 c1 cf 4f c3    movabs r10,0x2c34fcfc1e0
1e7:    02 00 00 
1ea:    41 52                   push   r10
1ec:    e9 ef 47 24 07          jmp    0x72449e0