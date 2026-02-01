#include <iostream>
#include <vector>

// Minimalized auto-range logic copy for host test
enum VoltageRange {RANGE_200MV, RANGE_2V, RANGE_20V, RANGE_200V, RANGE_1000V};

struct AutoRangeSim {
  float calibrationFactors[5];
  float overloadThresholds[5];
  VoltageRange currentRange;
  unsigned long lastChangeTime;
  unsigned long cooldownMs;
  AutoRangeSim() {
    currentRange = RANGE_20V;
    calibrationFactors[RANGE_200MV]=0.1; calibrationFactors[RANGE_2V]=1; calibrationFactors[RANGE_20V]=10; calibrationFactors[RANGE_200V]=100; calibrationFactors[RANGE_1000V]=500;
    overloadThresholds[RANGE_200MV]=0.25; overloadThresholds[RANGE_2V]=2.5; overloadThresholds[RANGE_20V]=25; overloadThresholds[RANGE_200V]=250; overloadThresholds[RANGE_1000V]=1200;
    lastChangeTime=0; cooldownMs=200;
  }
  bool step(float rawVoltage, unsigned long now) {
    if (now - lastChangeTime < cooldownMs) return false;
    float measured = rawVoltage * calibrationFactors[currentRange];
    float high = overloadThresholds[currentRange]*0.9f;
    float low = overloadThresholds[currentRange]*0.2f;
    VoltageRange newRange = currentRange;
    if (measured > high && currentRange < RANGE_1000V) newRange = (VoltageRange)(currentRange+1);
    if (measured < low && currentRange > RANGE_200MV) newRange = (VoltageRange)(currentRange-1);
    if (newRange != currentRange) { currentRange=newRange; lastChangeTime=now; return true; }
    return false;
  }
};

int main(){
  AutoRangeSim s;
  unsigned long now=0;
  // ramp rawVoltage such that measured will cross thresholds to trigger range change
  for (int i=0;i<1000;i++){
    float raw = i/1000.0f; // 0..1
    if (s.step(raw, now)) std::cout<<"Range changed at step "<<i<<" to "<<s.currentRange<<"\n";
    now += 50; // 50ms per step
  }
  std::cout<<"Final range: "<<s.currentRange<<"\n";
  return 0;
}
