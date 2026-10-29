/* Cocoa text receiver. No swizzling, event hooks or Blender ABI access. */
#import <Cocoa/Cocoa.h>

// Versioned Objective-C names allow different releases to coexist during hot reload.
#ifndef NCIMEClient
#define NCIMEClient NCIMEClient_1_4_0
#endif

typedef void (*NCIMECallback)(int kind, const char *text);

@interface NCIMEClient : NSTextView
@property(nonatomic, strong) NSResponder *previousResponder;
@property(nonatomic, strong) NSMutableIndexSet *consumedKeys;
@property(nonatomic, copy) NSString *committed;
@property(nonatomic) NSRect caretRect;
@property(nonatomic) NCIMECallback callback;
@property(nonatomic) BOOL stopped;
@end

@implementation NCIMEClient
- (BOOL)acceptsFirstResponder { return YES; }
- (BOOL)isOpaque { return NO; }
- (void)drawRect:(NSRect)rect { (void)rect; }
- (NSView *)hitTest:(NSPoint)point { (void)point; return nil; }
- (void)drawInsertionPointInRect:(NSRect)rect color:(NSColor *)color turnedOn:(BOOL)flag {
    (void)rect; (void)color; (void)flag;
}
- (void)emit:(int)kind text:(NSString *)text {
    if (!self.stopped && self.callback) self.callback(kind, text.UTF8String ?: "");
}
- (void)keyDown:(NSEvent *)event {
    const BOOL shortcut = event.modifierFlags & (NSEventModifierFlagCommand |
                                                 NSEventModifierFlagControl |
                                                 NSEventModifierFlagOption);
    const unsigned short key = event.keyCode;
    const BOOL navigation = key == 36 || key == 76 || key == 53 || key == 51 ||
                            key == 117 || (key >= 123 && key <= 126) || key == 50 || key == 48;
    // Keep a composition-confirming key consumed until release, including repeats.
    const BOOL wasConsumed = [self.consumedKeys containsIndex:key];
    if (!self.hasMarkedText && !wasConsumed && (shortcut || navigation)) {
        [self.previousResponder keyDown:event];
        return;
    }
    [self.consumedKeys addIndex:key];
    [super keyDown:event];
}
- (void)keyUp:(NSEvent *)event {
    if (![self.consumedKeys containsIndex:event.keyCode]) [self.previousResponder keyUp:event];
    [self.consumedKeys removeIndex:event.keyCode];
}
- (void)flagsChanged:(NSEvent *)event {
    [self.previousResponder flagsChanged:event];
}
- (void)doCommandBySelector:(SEL)selector {
    // Candidate confirmation is not node confirmation, even if the IME sends both.
    if (selector == @selector(insertNewline:) || selector == @selector(insertTab:)) return;
    if (selector == @selector(cancelOperation:)) {
        [self.inputContext discardMarkedText];
        self.string = self.committed ?: @"";
        self.selectedRange = NSMakeRange(self.string.length, 0);
        [self emit:2 text:@""];
        return;
    }
    [super doCommandBySelector:selector];
}
- (void)insertText:(id)value replacementRange:(NSRange)range {
    [super insertText:value replacementRange:range];
    self.committed = self.string;
    [self emit:4 text:self.committed];
}
- (void)setMarkedText:(id)value selectedRange:(NSRange)selected replacementRange:(NSRange)range {
    [super setMarkedText:value selectedRange:selected replacementRange:range];
    NSRange marked = self.markedRange;
    NSString *text = marked.location == NSNotFound ? @"" : [self.string substringWithRange:marked];
    [self emit:2 text:text];
}
- (void)unmarkText {
    [super unmarkText];
    [self emit:2 text:@""];
}
- (NSRect)firstRectForCharacterRange:(NSRange)range actualRange:(NSRangePointer)actual {
    if (actual) *actual = range;
    return [self.window convertRectToScreen:self.caretRect];
}
@end

static NCIMEClient *client;

int nc_ime_start(NCIMECallback callback) {
    if (![NSThread isMainThread] || client || !NSApp.keyWindow) {
        callback(3, "start: no key window, non-main thread or existing session");
        return 0;
    }
    NSWindow *window = NSApp.keyWindow;
    client = [[NCIMEClient alloc] initWithFrame:NSMakeRect(0, 0, 1, 1)];
    client.editable = YES;
    client.selectable = YES;
    client.drawsBackground = NO;
    client.richText = NO;
    client.automaticQuoteSubstitutionEnabled = NO;
    client.automaticDashSubstitutionEnabled = NO;
    client.automaticSpellingCorrectionEnabled = NO;
    client.automaticTextReplacementEnabled = NO;
    client.callback = callback;
    client.committed = @"";
    client.consumedKeys = [NSMutableIndexSet indexSet];
    client.previousResponder = window.firstResponder;
    [window.contentView addSubview:client];
    if (![window makeFirstResponder:client]) {
        callback(3, "start: makeFirstResponder refused");
        [client removeFromSuperview];
        client = nil;
        return 0;
    }
    return 1;
}

void nc_ime_sync(const char *query) {
    if (!client || client.hasMarkedText) return;
    NSString *text = [NSString stringWithUTF8String:query] ?: @"";
    if (![client.string isEqualToString:text]) {
        client.string = text;
        client.selectedRange = NSMakeRange(text.length, 0);
    }
    client.committed = text;
}

void nc_ime_caret(double x, double y, double width, double height) {
    if (!client) return;
    const double scale = client.window.backingScaleFactor;
    NSRect rect = NSMakeRect(x / scale, y / scale, width / scale, height / scale);
    if (!NSEqualRects(rect, client.caretRect)) {
        client.caretRect = rect;
        [client.inputContext invalidateCharacterCoordinates];
    }
}

int nc_ime_focused(void) {
    return client && client.window.isKeyWindow && client.window.firstResponder == client;
}

int nc_ime_reacquire(void) {
    if (nc_ime_focused()) return 1;
    // Mouse interaction may return focus to Blender, but never steal another field's focus.
    if (client && client.window.isKeyWindow &&
        client.window.firstResponder == client.previousResponder) {
        return [client.window makeFirstResponder:client];
    }
    return 0;
}

const char *nc_ime_input_source(void) {
    return client.inputContext.selectedKeyboardInputSource.UTF8String;
}

void nc_ime_stop(void) {
    if (!client || ![NSThread isMainThread]) return;
    client.stopped = YES;
    [client.inputContext discardMarkedText];
    if (client.window.firstResponder == client) {
        [client.window makeFirstResponder:client.previousResponder];
    }
    [client removeFromSuperview];
    client.previousResponder = nil;
    client.callback = NULL;
    client = nil;
}
