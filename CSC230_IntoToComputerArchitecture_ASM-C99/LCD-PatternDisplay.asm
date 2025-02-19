;
; a3part-D.asm
;
; Part D of assignment #3
;
;
; Student name: lexph
; Student ID:	
; Date of completed work: 2024-Mar-20
;
; **********************************
; Code provided for Assignment #3
;
; Author: Mike Zastre (2022-Nov-05)
;
; This skeleton of an assembly-language program is provided to help you 
; begin with the programming tasks for A#3. As with A#2 and A#1, there are
; "DO NOT TOUCH" sections. You are *not* to modify the lines within these
; sections. The only exceptions are for specific changes announced on
; Brightspace or in written permission from the course instruction.
; *** Unapproved changes could result in incorrect code execution
; during assignment evaluation, along with an assignment grade of zero. ***
;


; =============================================
; ==== BEGINNING OF "DO NOT TOUCH" SECTION ====
; =============================================
;
; In this "DO NOT TOUCH" section are:
; 
; (1) assembler direction setting up the interrupt-vector table
;
; (2) "includes" for the LCD display
;
; (3) some definitions of constants that may be used later in
;     the program
;
; (4) code for initial setup of the Analog-to-Digital Converter
;     (in the same manner in which it was set up for Lab #4)
;
; (5) Code for setting up three timers (timers 1, 3, and 4).
;
; After all this initial code, your own solutions's code may start
;

.cseg
.org 0
	jmp reset

; Actual .org details for this an other interrupt vectors can be
; obtained from main ATmega2560 data sheet
;
.org 0x22
	jmp timer1

; This included for completeness. Because timer3 is used to
; drive updates of the LCD display, and because LCD routines
; *cannot* be called from within an interrupt handler, we
; will need to use a polling loop for timer3.
;
; .org 0x40
;	jmp timer3

.org 0x54
	jmp timer4

.include "m2560def.inc"
.include "lcd.asm"

.cseg
#define CLOCK 16.0e6
#define DELAY1 0.01
#define DELAY3 0.1
#define DELAY4 0.5

#define BUTTON_RIGHT_MASK 0b00000001	
#define BUTTON_UP_MASK    0b00000010
#define BUTTON_DOWN_MASK  0b00000100
#define BUTTON_LEFT_MASK  0b00001000

#define BUTTON_RIGHT_ADC  0x032
#define BUTTON_UP_ADC     0x0b0   ; was 0x0c3
#define BUTTON_DOWN_ADC   0x160   ; was 0x17c
#define BUTTON_LEFT_ADC   0x22b
#define BUTTON_SELECT_ADC 0x316

.equ PRESCALE_DIV=1024   ; w.r.t. clock, CS[2:0] = 0b101

; TIMER1 is a 16-bit timer. If the Output Compare value is
; larger than what can be stored in 16 bits, then either
; the PRESCALE needs to be larger, or the DELAY has to be
; shorter, or both.
.equ TOP1=int(0.5+(CLOCK/PRESCALE_DIV*DELAY1))
.if TOP1>65535
.error "TOP1 is out of range"
.endif

; TIMER3 is a 16-bit timer. If the Output Compare value is
; larger than what can be stored in 16 bits, then either
; the PRESCALE needs to be larger, or the DELAY has to be
; shorter, or both.
.equ TOP3=int(0.5+(CLOCK/PRESCALE_DIV*DELAY3))
.if TOP3>65535
.error "TOP3 is out of range"
.endif

; TIMER4 is a 16-bit timer. If the Output Compare value is
; larger than what can be stored in 16 bits, then either
; the PRESCALE needs to be larger, or the DELAY has to be
; shorter, or both.
.equ TOP4=int(0.5+(CLOCK/PRESCALE_DIV*DELAY4))
.if TOP4>65535
.error "TOP4 is out of range"
.endif

reset:
; ***************************************************
; **** BEGINNING OF FIRST "STUDENT CODE" SECTION ****
; ***************************************************

; Anything that needs initialization before interrupts
; start must be placed here.
#define DASH 0x2D
#define ASTERISK 0x2A
#define RIGHT 0x52
#define UP    0x55
#define DOWN  0x44
#define LEFT  0x4C
#define SPACE 0x20
#define BUTTON_NONE_ADC 0x384


.def BOUNDARY_LOW = r0
.def BOUNDARY_HIGH = r1
.def DATAL = r24
.def DATAH = r25

; Initialize the stack
ldi temp, low(RAMEND)
out SPL, temp
ldi temp, high(RAMEND)
out SPH, temp


; ***************************************************
; ******* END OF FIRST "STUDENT CODE" SECTION *******
; ***************************************************

; =============================================
; ====  START OF "DO NOT TOUCH" SECTION    ====
; =============================================

	; initialize the ADC converter (which is needed
	; to read buttons on shield). Note that we'll
	; use the interrupt handler for timer 1 to
	; read the buttons (i.e., every 10 ms)
	;
	ldi temp, (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0)
	sts ADCSRA, temp
	ldi temp, (1 << REFS0)
	sts ADMUX, r16

	; Timer 1 is for sampling the buttons at 10 ms intervals.
	; We will use an interrupt handler for this timer.
	ldi r17, high(TOP1)
	ldi r16, low(TOP1)
	sts OCR1AH, r17
	sts OCR1AL, r16
	clr r16
	sts TCCR1A, r16
	ldi r16, (1 << WGM12) | (1 << CS12) | (1 << CS10)
	sts TCCR1B, r16
	ldi r16, (1 << OCIE1A)
	sts TIMSK1, r16

	; Timer 3 is for updating the LCD display. We are
	; *not* able to call LCD routines from within an 
	; interrupt handler, so this timer must be used
	; in a polling loop.
	ldi r17, high(TOP3)
	ldi r16, low(TOP3)
	sts OCR3AH, r17
	sts OCR3AL, r16
	clr r16
	sts TCCR3A, r16
	ldi r16, (1 << WGM32) | (1 << CS32) | (1 << CS30)
	sts TCCR3B, r16
	; Notice that the code for enabling the Timer 3
	; interrupt is missing at this point.

	; Timer 4 is for updating the contents to be displayed
	; on the top line of the LCD.
	ldi r17, high(TOP4)
	ldi r16, low(TOP4)
	sts OCR4AH, r17
	sts OCR4AL, r16
	clr r16
	sts TCCR4A, r16
	ldi r16, (1 << WGM42) | (1 << CS42) | (1 << CS40)
	sts TCCR4B, r16
	ldi r16, (1 << OCIE4A)
	sts TIMSK4, r16

	sei

; =============================================
; ====    END OF "DO NOT TOUCH" SECTION    ====
; =============================================

; ****************************************************
; **** BEGINNING OF SECOND "STUDENT CODE" SECTION ****
; ****************************************************

;--------------------------------------------------------------------
;====================================================================
; @Functions: MAIN 
; @brief:  Uses a polling loop and timer 3 to check if button is pressed
;		   If button is pressed increment counter based on character sequence
; @params: None
; @returns: None
start:
	
	;initialize the lcd display
	rcall lcd_init
	;initialize CURRENT_CHARSET_INDEX and TOP_ROW_CONTENT to base values
	rcall initialize_data_space

polling_loop:

	;load timer3's flag register
	in temp, TIFR3 
	;compare TIFR3 register with mask of OCF3A flag bit
	sbrs temp, OCF3A ;skip rjmp if OCF3A(6th) bit is set
	rjmp polling_loop ;else it's zero, continue polling
	
	push temp
	rcall set_button_press ;
	pop temp				;contains 1 if button is pressed, 0 if not pressed

	tst temp
	breq skip_counter
	rcall set_counter
skip_counter:
	
	;reset flag to be able to detect next TOP
	ldi temp, (1<<OCF3A)
	sts TIFR3, temp
	rjmp polling_loop
;=================end of main========================================
;--------------------------------------------------------------------

;====================================================================
; @Functions: initialize_data_space
; @brief:  sets our initial vectors to base characters
; @params: None
; @returns: None
initialize_data_space:
	push temp
	push r17
	push r18
	push r19
	;---------------
	;set TOP_LINE_CONTENT to all SPACES
	ldi temp, SPACE		
	ldi r17, low(TOP_LINE_CONTENT)		;address for TOP_LINE_CONTENT
	ldi r18, high(TOP_LINE_CONTENT)
	ldi r19, 16			;offset range - 16 bytes total
	push temp
	push r17
	push r18
	push r19
	rcall clear_data_space
	pop r19
	pop r18
	pop r17
	pop temp
	;set CURRENT_CHARSET_INDEX to all zeroes
	ldi temp, 0		
	ldi r17, low(CURRENT_CHARSET_INDEX)		;address for TOP_LINE_CONTENT
	ldi r18, high(CURRENT_CHARSET_INDEX)
	ldi r19, 16			;offset range - 16 bytes total
	push temp
	push r17
	push r18
	push r19
	rcall clear_data_space
	pop r19
	pop r18
	pop r17
	pop temp
	;zero char index
	ldi temp, 0
	sts CURRENT_CHAR_INDEX, temp
	;---------------
	pop r19
	pop r18
	pop r17
	pop temp

	ret
;====================end of initialize_data_space====================

;====================================================================
; @Functions: clear_data_space
; @brief: clear data space from input address to offset
; @params: 4 bytes pushed onto stack
;		   - 1 byte represents char used to for setting - pushed first
;		   - 2 bytes representing start address. Low pushed second, then high pushed third
;		   - 1 byte representing offset - pushed last
; @returns: None
clear_data_space:
	.set PARAM_OFFSET = 11
	push temp		;offset that was pushed onto stack
	push ZL			;pointer to data space to be cleared
	push ZH
	push YL			;pointer to variables on stack
	push YH	
	push r17		;counter
	push r18		;holds a character to be stored in data space
	;---------------
	in YL, SPL
	in YH, SPH
	ldd temp, Y + PARAM_OFFSET
	ldd ZL, Y + PARAM_OFFSET + 2	
	ldd ZH, Y + PARAM_OFFSET + 1
	ldd r18, Y + PARAM_OFFSET + 3
	ldi r17, 0		;set counter to zero

	
loop_clear_data_space:
	cp r17, temp	;compare counter to offset
	breq exit_clear_data_space
	st Z+, r18		;store character at data space pointed to by Z
	inc r17
	rjmp loop_clear_data_space
exit_clear_data_space:
	;---------------
	pop r18
	pop r17
	pop YH
	pop YL
	pop ZH
	pop ZL
	pop temp
	ret

;====================================================================
; @Functions: set_button_press
; @brief: Sets LCD panel lower right panel with '*' if button was pressed, '-' otherwise
; @params: one byte pushed onto stack that will be modified
; @returns: modified stack value indicating if button is pressed
set_button_press:	
	.set PARAM_OFFSET = 8
	push temp
	push YL
	push YH
	push r18		;holds return value indicating button pressed
	;--------------
	in YL, SPL
	in YH, SPH
	ldd r18, Y + PARAM_OFFSET

	;set lcd row, col [1,15] 
	ldi temp, 1 
	push temp ;row 1
	ldi temp, 15
	push temp ;col 15
	rcall lcd_gotoxy
	pop temp
	pop temp
	;--Update LCD--
	lds temp, BUTTON_IS_PRESSED ;load button press flag from data space
	
	tst temp
	breq button_not_pressed ;
	ldi r18, 1			;set return as 1
	ldi temp, ASTERISK	;if button pressed 
	push temp			;then output '*'
	rcall lcd_putchar	;to lcd	
	pop temp
	;rcall set_counter ;increment/decrement counter
	rcall test_which_button ;button was pressed, check which one
	rjmp end_pressed_button
button_not_pressed:	
	ldi r18, 0			;set return as zero
	ldi temp, DASH		;else -> output '-'
	push temp			;to lcd
	rcall lcd_putchar
	pop temp
end_pressed_button:		
	;-------------
	pop r18
	pop YH
	pop YL
	pop temp

	ret
;====================End of set_button_press============================

;====================================================================
; @Functions: set_counter
; @brief: Outputs current top row content at char_index
; @params: None
; @returns: None
set_counter:
	;load top row char at index 0
	;output every time this gets called
	push r17
	push r0
	push ZL
	push ZH
	push r18
	push temp
	;----------------
	lds r17, CURRENT_CHAR_INDEX		;load with index offset of top row		
	clr r0							;clr r0 for add
	ldi ZL, low(TOP_LINE_CONTENT)
	ldi ZH, high(TOP_LINE_CONTENT)

	add ZL, r17						;offset is at max 15 so 1 byte has plenty of rm
	adc ZH, r0
	ld r18, Z						;Z still points to first byte in top row content, load char
	cpi r18, 0
	breq exit_set_counter			;don't print out null terminator
	ldi temp, 0						;for row number, never changes
	push temp						;push row #
	push r17						;r17 contains col #, push col
	rcall lcd_gotoxy				;set gotoxy
	pop r17
	pop temp
	push r18						;push char from top row content at index
	rcall lcd_putchar				;output to lcd
	pop r18
exit_set_counter:
	;----------------
	pop temp
	pop r18
	pop ZH
	pop ZL 
	pop r0
	pop r17
	
	ret

;====================End of set_counter=================================

;====================================================================
; @Functions: test_which_button
; @brief: Checks which button was pressed calls set char for the lcd 
;		  panel that displays that button
; @params: None
; @returns: None
test_which_button:
	push temp
	push r17
	push r18
	push r19
	;--------------
		
	;Only output char if different from last
	lds r18, LAST_BUTTON_PRESSED
	lds r19, CURRENT_BUTTON_PRESSED
	cp r18, r19
	breq last_button_pressed_same
	;----if current is 'R----
	cpi r19, RIGHT
	brne skip_char_R
	ldi temp, 1 
	ldi r17, 3
	push temp ;row 1
	push r17 ;col 3
	rcall set_char
	pop r17
	pop temp
	rjmp set_char_end
skip_char_R:
	;---else if current is 'U'--
	cpi r19, UP
	brne skip_char_U
	ldi temp, 1 
	ldi r17, 2
	push temp ;row 1
	push r17 ;col 2
	rcall set_char
	pop r17
	pop temp
	rjmp set_char_end
skip_char_U:	
	;---else if current is 'D'---
	cpi r19, DOWN
	brne skip_char_D
	ldi temp, 1 
	ldi r17, 1
	push temp ;row 1
	push r17 ;col 2
	rcall set_char
	pop r17
	pop temp
	rjmp set_char_end
skip_char_D:
	;---else if current is 'L'---	
	cpi r19, LEFT
	brne set_char_end
	ldi temp, 1 
	ldi r17, 0
	push temp ;row 1
	push r17 ;col 2
	rcall set_char
	pop r17
	pop temp
	rjmp set_char_end
set_char_end:
	;Update last button pressed
	lds r19, CURRENT_BUTTON_PRESSED
	sts LAST_BUTTON_PRESSED, r19
last_button_pressed_same:
	pop r19
	pop r18
	pop r17
	pop temp
	;-----------------
	ret

;====================================================================
; @Functions: set_char
; @brief: Clear bottom row, output current button to lcd
; @params: two variables pushed onto stack, row and col
; @returns: None
set_char:	
	.set PARAM_OFFSET = 9
	push temp	 ;row
	push r17	 ;col
	push YH
	push YL
	push r19	 ;Current Button Pressed
	;--------
	in YH, SPH
	in YL, SPL
	ldd temp,  Y + 1 + PARAM_OFFSET		;load row variable pushed onto stack
	ldd r17, Y + PARAM_OFFSET			;load col variable pushed onto stack

	;---clear btm row---
	ldi r19, 1		
	push r19
	rcall clear_lcd_row
	pop r19

	lds r19, CURRENT_BUTTON_PRESSED		;load current button pressed

	push temp ;row 
	push r17 ;col 
	rcall lcd_gotoxy
	pop r17
	pop temp
	;output character
	push r19
	rcall lcd_putchar
	pop r19
	;--------
	pop r19
	pop YL
	pop YH
	pop r17
	pop temp

	ret
;====================End of set_char==================================

;====================================================================
; @Function: clear_lcd_row
; @brief: Clears bottom row of lcd 
; @params: row number pushed onto stack
; @returns: None
clear_lcd_row:
	.set PARAM_OFFSET = 9
	push temp
	push r17		;row		
	push r18		;col
	push YL			;pointer to value on stack
	push YH
	;----------------
	in YL, SPL
	in YH, SPH		
	ldd r17, Y + PARAM_OFFSET	;contain row # pushed onto stack
	ldi temp, 0		;counter
loop:
	cpi temp, 16		;loop max, loops from 0 - 15, breaks when 16
	breq exit_clear_lcd_row
	mov r18, temp		;copy counter into col
	push r17			;push row
	push r18			;push col
	rcall lcd_gotoxy	;set lcd panel
	pop r18
	pop r17
	ldi r18, SPACE		;load with space
	push r18
	rcall lcd_putchar	;output space to panel
	pop r18
	inc temp			;increment counter
	rjmp loop			;continue looping

exit_clear_lcd_row:
	;----------------
	pop YH
	pop YL
	pop r18
	pop r17
	pop temp

	ret
;====================End of clear_lcd_row==================================

;====================================================================
; @ISR: timer1
; @brief: Updates BUTTON_IS_PRESSED with 1 if pressed, 0 otherwise 
; @params: None
; @returns: None
timer1:
	push temp
	in temp, SREG
	push temp
	push BOUNDARY_LOW
	push BOUNDARY_HIGH
	push DATAL
	push DATAH
	;----------

	;Set ADC start bit, wait until set
	lds temp, ADCSRA
	ori temp, 0x40
	sts ADCSRA, temp ;set start bit
wait: lds temp, ADCSRA
	andi temp, 0x40
	brne wait ;

	;retrieve adc converted input data
	lds DATAL, ADCL
	lds DATAH, ADCH
	
	;---Load "RIGHT" button ADC max---
	ldi temp, low(BUTTON_RIGHT_ADC)
	mov BOUNDARY_LOW, temp
	ldi temp, high(BUTTON_RIGHT_ADC)
	mov BOUNDARY_HIGH, temp
	cp DATAL, BOUNDARY_LOW
	cpc DATAH, BOUNDARY_HIGH
	;(branch if same or higher)
	brsh skip_right ;if ADC >= boundary, button was not pressed
	ldi temp, 1
	sts BUTTON_IS_PRESSED, temp
	ldi temp, RIGHT
	sts CURRENT_BUTTON_PRESSED, temp ;set current to "R"
	rjmp timer1_end
skip_right:
	;---Load "UP" button ADC max---
	ldi temp, low(BUTTON_UP_ADC)
	mov BOUNDARY_LOW, temp
	ldi temp, high(BUTTON_UP_ADC)
	mov BOUNDARY_HIGH, temp
	cp DATAL, BOUNDARY_LOW
	cpc DATAH, BOUNDARY_HIGH
	;(branch if same or higher)
	brsh skip_up ;if ADC >= boundary, button was not pressed
	ldi temp, 1
	sts BUTTON_IS_PRESSED, temp
	ldi temp, UP
	sts CURRENT_BUTTON_PRESSED, temp ;set current to "U"
	rjmp timer1_end
skip_up:
	;---Load "DOWN" button ADC max---
	ldi temp, low(BUTTON_DOWN_ADC)
	mov BOUNDARY_LOW, temp
	ldi temp, high(BUTTON_DOWN_ADC)
	mov BOUNDARY_HIGH, temp
	cp DATAL, BOUNDARY_LOW
	cpc DATAH, BOUNDARY_HIGH
	;(branch if same or higher)
	brsh skip_down ;if ADC >= boundary, button was not pressed
	ldi temp, 1
	sts BUTTON_IS_PRESSED, temp
	ldi temp, DOWN
	sts CURRENT_BUTTON_PRESSED, temp ;set DOWN "D"
	rjmp timer1_end
skip_down:
	;---Load "LEFT" button ADC max---
	ldi temp, low(BUTTON_LEFT_ADC)
	mov BOUNDARY_LOW, temp
	ldi temp, high(BUTTON_LEFT_ADC)
	mov BOUNDARY_HIGH, temp
	cp DATAL, BOUNDARY_LOW
	cpc DATAH, BOUNDARY_HIGH
	;(branch if same or higher)
	brsh skip_left ;if ADC >= boundary, button was not pressed
	ldi temp, 1
	sts BUTTON_IS_PRESSED, temp
	ldi temp, LEFT
	sts CURRENT_BUTTON_PRESSED, temp ;set LEFT "L"
	rjmp timer1_end
skip_left:
	;---No button selected---
	ldi temp, 0 
	sts BUTTON_IS_PRESSED, temp ;else set button to zero
timer1_end:
	;----------
	pop DATAH
	pop DATAL
	pop BOUNDARY_HIGH
	pop BOUNDARY_LOW
	pop temp
	out SREG, temp
	pop temp

	reti
;====================End of timer1==================================

; timer3:
;
; Note: There is no "timer3" interrupt handler as you must use
; timer3 in a polling style (i.e. it is used to drive the refreshing
; of the LCD display, but LCD functions cannot be called/used from
; within an interrupt handler).


;====================================================================
; @ISR: timer4
; @brief: If button is pressed, updates CURRENT_CHARSET_INDEX and updates TOP_LINE_CONTENT
;	  with new character from char sequence at updated index.
; @params: None
; @returns: None
timer4:
	push temp		;save previous temp
	in temp, SREG
	push temp		;save SREG
	push r17 		;CURRENT_CHAR_INDEX
	push ZH			;Points either at byte in sequence, 
	push ZL			;or byte in charset_index
	push YH			;Points at top_line_content
	push YL
	push r0			;zero the register for adding
	push r18		;holds index from current_charset_index
	push r19		;flag for first UP button press

	;---if(button_is_pressed)--
	clr r0		
	lds temp, BUTTON_IS_PRESSED		;load button pressed flag
	tst temp
	breq exit_timer4_helper			;exit if button not pressed

	lds r17, CURRENT_CHAR_INDEX

	;---Set up initial pointers at current_char_index----
	ldi YL, low(TOP_LINE_CONTENT)		;Pointer to start of TOP_LINE_CONTENT
	ldi YH, high(TOP_LINE_CONTENT)
	add YL, r17		;zero, points to the first byte in top_line_content
	adc YH, r0		;zero register

	ldi ZL, low(CURRENT_CHARSET_INDEX)	;Pointer to start of CURRENT_CHARSET_INDEX
	ldi ZH, high(CURRENT_CHARSET_INDEX)
	add ZL, r17		;zero, points to the first byte in current_charset_index
	adc ZH, r0	 	;zero register
	clr r0

	;---if(button 'U' is pressed)---
	ld r19, Y		;load top row at char index. If SPACE, then it will be the first up button
	lds temp, CURRENT_BUTTON_PRESSED
	cpi temp, UP
	brne t4_skip_up
	ld temp, Y				;holds char last
	cpi temp, 0 			;check if at max count
	breq exit_timer4		;don't increment if at max
	ld r18, Z				;load charset index
	cpi r19, SPACE			
	breq first_up			;skip increment if at min index
	inc r18					;increment by one, holds new index
first_up:
	st Z, r18				;update current_charset_index
	ldi ZL, low(AVAILABLE_CHARSET<<1)	;pointer to char sequence
	ldi ZH, high(AVAILABLE_CHARSET<<1)	
	clr r0
	add ZL, r18				;Z now points to char at new index in char sequence
	adc ZH, r0
	lpm temp, Z 			;load char from sequence at new index
	st Y, temp				;store char in top line content
	rjmp exit_timer4
t4_skip_up:
	
	;---if(button 'D' is pressed)---
	lds temp, CURRENT_BUTTON_PRESSED
	cpi temp, DOWN
	brne t4_skip_down		
	ld r18, Z				;holds the index at current_charset_index
	tst r18 				;check if index is zero
	breq zeroed_clear_count		;don't decrement if index is already at lowest
	dec r18					;decrement by one, holds new index
	st Z, r18				;update current_charset_index
	ldi ZL, low(AVAILABLE_CHARSET<<1)	;pointer to char sequence
	ldi ZH, high(AVAILABLE_CHARSET<<1)	
	clr r0
	add ZL, r18				;Z now points to char at new index in char sequence
	adc ZH, r0
	lpm temp, Z 			;load char from sequence at new index
	st Y, temp				;store char in top line content
	rjmp exit_timer4
zeroed_clear_count:	
	ldi temp, SPACE			;prev was already at min, clear the panel
	st Y, temp
exit_timer4_helper:			;helper for higher branching to be able to jump to timer end
	rjmp exit_timer4
t4_skip_down:
	
	;---if(button 'R' is pressed)---
	lds temp, CURRENT_BUTTON_PRESSED
	cpi temp, RIGHT
	brne t4_skip_right
	;max shift right of 15 [0,15]
	lds temp, CURRENT_CHAR_INDEX
	cpi temp, 15					;if at max index, exit
	breq exit_timer4
	inc temp						;else increment char_index
	sts CURRENT_CHAR_INDEX, temp
	rjmp exit_timer4
t4_skip_right:

	;---if(button 'L' is pressed)---
	lds temp, CURRENT_BUTTON_PRESSED
	cpi temp, LEFT
	brne t4_skip_left
	;max shift left is 0
	lds temp, CURRENT_CHAR_INDEX
	tst temp						;tests if zero
	breq exit_timer4
	dec temp						;else decrement char_index
	sts CURRENT_CHAR_INDEX, temp	;store updated char_index in data space 	
t4_skip_left:

exit_timer4:
	;--------------
	pop r19
	pop r18
	pop r0
	pop YL
	pop YH
	pop ZL
	pop ZH
	pop r17
	pop temp
	out SREG, temp
	pop temp

	reti
;====================End of timer4==================================


; ****************************************************
; ******* END OF SECOND "STUDENT CODE" SECTION *******
; ****************************************************


; =============================================
; ==== BEGINNING OF "DO NOT TOUCH" SECTION ====
; =============================================

; r17:r16 -- word 1
; r19:r18 -- word 2
; word 1 < word 2? return -1 in r25
; word 1 > word 2? return 1 in r25
; word 1 == word 2? return 0 in r25
;
compare_words:
	; if high bytes are different, look at lower bytes
	cp r17, r19
	breq compare_words_lower_byte

	; since high bytes are different, use these to
	; determine result
	;
	; if C is set from previous cp, it means r17 < r19
	; 
	; preload r25 with 1 with the assume r17 > r19
	ldi r25, 1
	brcs compare_words_is_less_than
	rjmp compare_words_exit

compare_words_is_less_than:
	ldi r25, -1
	rjmp compare_words_exit

compare_words_lower_byte:
	clr r25
	cp r16, r18
	breq compare_words_exit

	ldi r25, 1
	brcs compare_words_is_less_than  ; re-use what we already wrote...

compare_words_exit:
	ret

.cseg
AVAILABLE_CHARSET: .db "abcdefghijklmnopqrstuvwxyz0123456789!", 0


.dseg

BUTTON_IS_PRESSED: .byte 1			; updated by timer1 interrupt, used by LCD update loop
LAST_BUTTON_PRESSED: .byte 1        ; updated by timer1 interrupt, used by LCD update loop

TOP_LINE_CONTENT: .byte 16			; updated by timer4 interrupt, used by LCD update loop
CURRENT_CHARSET_INDEX: .byte 16		; updated by timer4 interrupt, used by LCD update loop
CURRENT_CHAR_INDEX: .byte 1			; ; updated by timer4 interrupt, used by LCD update loop


; =============================================
; ======= END OF "DO NOT TOUCH" SECTION =======
; =============================================


; ***************************************************
; **** BEGINNING OF THIRD "STUDENT CODE" SECTION ****
; ***************************************************

.dseg
CURRENT_BUTTON_PRESSED: .byte 1
; If you should need additional memory for storage of state,
; then place it within the section. However, the items here
; must not be simply a way to replace or ignore the memory
; locations provided up above.


; ***************************************************
; ******* END OF THIRD "STUDENT CODE" SECTION *******
; ***************************************************
