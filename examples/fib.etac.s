

	.global fib
	.text
fib:
	pushq %rbp
	movq %rsp, %rbp
	subq $64, %rsp
	movq %rdi, -8(%rbp)
.Lfib0:
	movq $0, %rax
	movq -8(%rbp), %r11
	subq %rax, %r11
	movq %r11, %rax
	movq %rax, %r11
	cmpq $0, %r11
	jz .Lfib6
	jmp .Lfib1 
.Lfib1:
	movq $1, %rax
	movq -8(%rbp), %r11
	subq %rax, %r11
	movq %r11, %rax
	movq %rax, %r11
	cmpq $0, %r11
	jz .Lfib4
	jmp .Lfib2 
.Lfib2:
	movq $1, %rax
	movq -8(%rbp), %r11
	subq %rax, %r11
	movq %r11, %rax
	movq %rax, %rdi
	pushq %rax
	callq fib
	movq %rax, %rsi
	movq $2, %rax
	movq -8(%rbp), %r11
	subq %rax, %r11
	movq %r11, %rax
	movq %rax, %rdi
	pushq %rax
	callq fib
	movq %rax, %rax
	movq %rsi, %r11
	addq %rax, %r11
	movq %r11, %rdi
	movq %rdi, %r11
	movq %r11, %rax
	jmp .Lfib7 
.Lfib3:
	jmp .Lfib5 
.Lfib4:
	movq $1, %rdi
	movq %rdi, %r11
	movq %r11, %rax
	jmp .Lfib7 
.Lfib5:
	jmp .Lfib7 
.Lfib6:
	movq $0, %rdi
	movq %rdi, %r11
	movq %r11, %rax
	jmp .Lfib7 
.Lfib7:
	movq %rax, %rax
	jmp .Lexit


	.global main
	.text
main:
	pushq %rbp
	movq %rsp, %rbp
	subq $0, %rsp
.Lmain0:
	movq $0, %rdi
	movq %rdi, %r11
	movq %r11, %rax
	jmp .Lmain1 
.Lmain1:
	movq $10, %rdi
	movq %rax, %r11
	subq %rdi, %r11
	movq %r11, %rdi
	movq %rdi, %r11
	cmpq $0, %r11
	jl .Lmain2
	jmp .Lmain3 
.Lmain2:
	movq %rax, %rdi
	pushq %rax
	callq fib
	movq %rax, %rdi
	movq %rdi, %rdi
	pushq %rax
	callq __bx_print_int
	movq $1, %rdi
	movq %rax, %r11
	addq %rdi, %r11
	movq %r11, %rdi
	movq %rdi, %r11
	movq %r11, %rax
	jmp .Lmain1 
.Lmain3:
	xorq %rax, %rax
	jmp .Lexit
.Lexit:
	movq %rbp, %rsp
	popq %rbp
	retq
