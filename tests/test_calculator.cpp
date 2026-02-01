#include <iostream>
#include <cmath>
#include <cstring>

// Minimal copies of parse helpers for host tests (adapted from firmware CalculatorEngine)
static void skipWhitespace(const char* expr, int& index) {
  while (expr[index] == ' ' || expr[index] == '\t' || expr[index] == '\n' || expr[index] == '\r') index++;
}

// Forward declarations
float parseExpression(const char* expr, int& index, float x_val);
float parseTerm(const char* expr, int& index, float x_val);
float parsePower(const char* expr, int& index, float x_val);
float parseFactor(const char* expr, int& index, float x_val);
float parseNumber(const char* expr, int& index);

float evaluateFunction(const char* name, float argument) {
  if (strcmp(name, "sin") == 0) return sin(argument);
  if (strcmp(name, "cos") == 0) return cos(argument);
  if (strcmp(name, "sqrt") == 0) return sqrt(argument);
  return NAN;
}

float parseExpression(const char* expr, int& index, float x_val) {
  skipWhitespace(expr, index);
  float value = parseTerm(expr, index, x_val);
  skipWhitespace(expr, index);
  while (expr[index] == '+' || expr[index] == '-') {
    char op = expr[index++];
    skipWhitespace(expr, index);
    float nextValue = parseTerm(expr, index, x_val);
    if (op == '+') value += nextValue; else value -= nextValue;
    skipWhitespace(expr, index);
  }
  return value;
}

float parseTerm(const char* expr, int& index, float x_val) {
  skipWhitespace(expr, index);
  float value = parsePower(expr, index, x_val);
  skipWhitespace(expr, index);
  while (expr[index] == '*' || expr[index] == '/') {
    char op = expr[index++]; skipWhitespace(expr, index);
    float nextValue = parsePower(expr, index, x_val);
    if (op == '*') value *= nextValue; else value = (nextValue != 0) ? value / nextValue : NAN;
    skipWhitespace(expr, index);
  }
  return value;
}

float parsePower(const char* expr, int& index, float x_val) {
  skipWhitespace(expr, index);
  float value = parseFactor(expr, index, x_val);
  skipWhitespace(expr, index);
  if (expr[index] == '^') {
    index++; skipWhitespace(expr, index);
    float exponent = parsePower(expr, index, x_val);
    return pow(value, exponent);
  }
  return value;
}

float parseFactor(const char* expr, int& index, float x_val) {
  skipWhitespace(expr, index);
  if (expr[index] == '(') { index++; float v = parseExpression(expr, index, x_val); if (expr[index] == ')') index++; return v; }
  if (expr[index] == 'x') { index++; return x_val; }
  if (isalpha(expr[index])) {
    char fn[16]; int fi = 0; while (isalpha(expr[index]) && fi < (int)(sizeof(fn)-1)) fn[fi++] = expr[index++]; fn[fi] = '\0'; skipWhitespace(expr, index);
    if (expr[index] == '(') { index++; float arg = parseExpression(expr, index, x_val); if (expr[index] == ')') index++; return evaluateFunction(fn, arg); }
    if (strcmp(fn, "pi") == 0) return 3.14159f; if (strcmp(fn, "e") == 0) return 2.71828f;
  }
  return parseNumber(expr, index);
}

float parseNumber(const char* expr, int& index) {
  skipWhitespace(expr, index);
  float value = 0, decimal = 0, divisor = 1; bool hasDecimal = false; bool negative=false;
  if (expr[index] == '-') { negative=true; index++; } else if (expr[index] == '+') index++;
  bool any=false;
  while ((expr[index] >= '0' && expr[index] <= '9') || expr[index] == '.') {
    any = true;
    if (expr[index] == '.') { hasDecimal = true; index++; }
    else if (!hasDecimal) { value = value*10 + (expr[index]-'0'); index++; }
    else { decimal = decimal*10 + (expr[index]-'0'); divisor *= 10; index++; }
  }
  if (!any) return NAN;
  value += decimal / divisor; return negative?-value:value;
}

int main() {
  struct Test { const char* expr; float expected; } tests[] = {
    {"1+2*3", 7}, {"(1+2)*3", 9}, {"sin(pi/2)", 1}, {"sqrt(4)+2", 4}
  };
  int failed=0;
  for (auto &t: tests) {
    int idx=0; float res = parseExpression(t.expr, idx, 0);
    std::cout << t.expr << " => " << res << " (expected " << t.expected << ")\n";
    if (fabs(res - t.expected) > 1e-3) failed++;
  }
  if (failed) std::cout << failed << " test(s) failed.\n"; else std::cout << "All calculator tests passed.\n";
  return failed;
}
