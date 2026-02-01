#ifndef CALCULATOR_ENGINE_H
#define CALCULATOR_ENGINE_H

#include <Arduino.h>
#include <math.h>
#include "smart_oscilloscope.h"

class CalculatorEngine {
private:
  char inputBuffer[256];
  int inputIndex;
  float result;
  bool hasResult;
  
  // Graph plotting
  float graphData[100]; // Store up to 100 points for graph
  int graphDataCount;
  
public:
  CalculatorEngine();
  bool initialize();
  float evaluateExpression(const char* expression, float x_val = 0.0);
  bool plotGraph(const char* function, float xMin, float xMax, int points = 50);
  float* getGraphData(int& count);
  void clearInput();
  void addToInput(char c);
  const char* getInputBuffer();
  float getResult();
  bool hasValidResult();
  void calculate();
  float parseExpression(const char* expr, int& index, float x_val);
  float parseTerm(const char* expr, int& index, float x_val);
  float parsePower(const char* expr, int& index, float x_val);
  float parseFactor(const char* expr, int& index, float x_val);
  float parseNumber(const char* expr, int& index);
  float evaluateFunction(const char* name, float argument);
};

#endif // CALCULATOR_ENGINE_H