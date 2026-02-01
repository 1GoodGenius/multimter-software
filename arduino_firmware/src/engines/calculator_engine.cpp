#include "calculator_engine.h"
#include <ctype.h>
#include <string.h>

CalculatorEngine::CalculatorEngine() {
  inputIndex = 0;
  result = 0.0;
  hasResult = false;
  graphDataCount = 0;
  clearInput();
}

bool CalculatorEngine::initialize() {
  return true;
}

static inline void skipWhitespace(const char* expr, int& index) {
  while (expr[index] == ' ' || expr[index] == '\t' || expr[index] == '\n' || expr[index] == '\r') index++;
}

float CalculatorEngine::evaluateExpression(const char* expression, float x_val) {
  int index = 0;
  skipWhitespace(expression, index);
  result = parseExpression(expression, index, x_val);
  hasResult = !isnan(result);
  return result;
}

bool CalculatorEngine::plotGraph(const char* function, float xMin, float xMax, int points) {
  if (points <= 0 || points > 100) return false;
  
  graphDataCount = points;
  float step = (xMax - xMin) / (points - 1);
  
  for (int i = 0; i < points; i++) {
    float x = xMin + i * step;
    // Evaluate the expression for the current value of x
    graphData[i] = evaluateExpression(function, x);
  }
  
  return true;
}

float* CalculatorEngine::getGraphData(int& count) {
  count = graphDataCount;
  return graphData;
}

void CalculatorEngine::clearInput() {
  inputIndex = 0;
  inputBuffer[0] = '\0';
  hasResult = false;
}

void CalculatorEngine::addToInput(char c) {
  if (inputIndex < (int)sizeof(inputBuffer) - 1) {
    inputBuffer[inputIndex++] = c;
    inputBuffer[inputIndex] = '\0';
  }
}

const char* CalculatorEngine::getInputBuffer() {
  return inputBuffer;
}

float CalculatorEngine::getResult() {
  return result;
}

bool CalculatorEngine::hasValidResult() {
  return hasResult;
}

void CalculatorEngine::calculate() {
  evaluateExpression(inputBuffer);
}

float CalculatorEngine::parseExpression(const char* expr, int& index, float x_val) {
  skipWhitespace(expr, index);
  float value = parseTerm(expr, index, x_val);
  skipWhitespace(expr, index);
  
  while (expr[index] == '+' || expr[index] == '-') {
    char op = expr[index++];
    skipWhitespace(expr, index);
    float nextValue = parseTerm(expr, index, x_val);
    
    if (op == '+') {
      value += nextValue;
    } else {
      value -= nextValue;
    }
    skipWhitespace(expr, index);
  }
  
  return value;
}

float CalculatorEngine::parseTerm(const char* expr, int& index, float x_val) {
  skipWhitespace(expr, index);
  float value = parsePower(expr, index, x_val);
  skipWhitespace(expr, index);
  
  while (expr[index] == '*' || expr[index] == '/') {
    char op = expr[index++];
    skipWhitespace(expr, index);
    float nextValue = parsePower(expr, index, x_val);
    
    if (op == '*') {
      value *= nextValue;
    } else {
      if (nextValue != 0) {
        value /= nextValue;
      } else {
        value = NAN; // Use Not-a-Number for division by zero
      }
    }
    skipWhitespace(expr, index);
  }
  
  return value;
}

float CalculatorEngine::parsePower(const char* expr, int& index, float x_val) {
  skipWhitespace(expr, index);
  float value = parseFactor(expr, index, x_val);
  skipWhitespace(expr, index);
  
  if (expr[index] == '^') {
    index++;
    skipWhitespace(expr, index);
    float exponent = parsePower(expr, index, x_val); // Recurse for right-associativity
    return pow(value, exponent);
  }
  
  return value;
}

float CalculatorEngine::parseFactor(const char* expr, int& index, float x_val) {
  skipWhitespace(expr, index);
  // Handle parentheses
  if (expr[index] == '(') {
    index++; // Skip '('
    float value = parseExpression(expr, index, x_val);
    skipWhitespace(expr, index);
    if (expr[index] == ')') {
      index++; // Skip ')'
    }
    return value;
  }

  // Handle variable 'x'
  if (expr[index] == 'x') {
    index++;
    return x_val;
  }
  
  // Handle functions by name
  if (isalpha(expr[index])) {
    // Read function name
    char fn[16];
    int fi = 0;
    while (isalpha(expr[index]) && fi < (int)(sizeof(fn) - 1)) {
      fn[fi++] = expr[index++];
    }
    fn[fi] = '\0';
    skipWhitespace(expr, index);
    if (expr[index] == '(') {
      index++; // skip '('
      float arg = parseExpression(expr, index, x_val);
      skipWhitespace(expr, index);
      if (expr[index] == ')') index++;
      return evaluateFunction(fn, arg);
    }
    // If no parentheses, treat as variable or constant (e.g., 'pi')
    if (strcmp(fn, "pi") == 0) return 3.14159265358979323846f;
    if (strcmp(fn, "e") == 0) return 2.71828182845904523536f;
  }
  
  return parseNumber(expr, index);
}

float CalculatorEngine::parseNumber(const char* expr, int& index) {
  skipWhitespace(expr, index);
  float value = 0.0f;
  float decimal = 0.0f;
  float divisor = 1.0f;
  bool hasDecimal = false;
  
  // Handle optional leading sign
  bool negative = false;
  if (expr[index] == '-') {
    negative = true;
    index++;
  } else if (expr[index] == '+') {
    index++;
  }

  bool anyDigit = false;
  while ((expr[index] >= '0' && expr[index] <= '9') || expr[index] == '.') {
    anyDigit = true;
    if (expr[index] == '.') {
      hasDecimal = true;
      index++;
    } else if (!hasDecimal) {
      value = value * 10 + (expr[index] - '0');
      index++;
    } else {
      decimal = decimal * 10 + (expr[index] - '0');
      divisor *= 10.0f;
      index++;
    }
  }
  
  if (!anyDigit) return NAN; // invalid number
  value += decimal / divisor;
  return negative ? -value : value;
}

float CalculatorEngine::evaluateFunction(const char* name, float argument) {
  if (strcmp(name, "sin") == 0) return sin(argument);
  if (strcmp(name, "cos") == 0) return cos(argument);
  if (strcmp(name, "tan") == 0) return tan(argument);
  if (strcmp(name, "sqrt") == 0) return sqrt(argument);
  if (strcmp(name, "log") == 0) return log(argument);
  if (strcmp(name, "exp") == 0) return exp(argument);
  if (strcmp(name, "abs") == 0) return fabs(argument);
  // Unknown function returns NAN
  return NAN;
}