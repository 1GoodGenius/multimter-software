#include <iostream>

// Minimal trigger logic test
enum TriggerEdge {TRIGGER_RISING, TRIGGER_FALLING, TRIGGER_BOTH};

bool checkTrigger(float lastValue, float value, float level, TriggerEdge edge) {
  bool triggered=false;
  switch (edge) {
    case TRIGGER_RISING: triggered = (lastValue <= level && value > level); break;
    case TRIGGER_FALLING: triggered = (lastValue >= level && value < level); break;
    case TRIGGER_BOTH: triggered = ((lastValue <= level && value > level) || (lastValue >= level && value < level)); break;
  }
  return triggered;
}

int main(){
  float last=0.0f; float level=0.5f; bool fired=false;
  for (int i=0;i<10;i++){ float v = i/10.0f; if (!fired && checkTrigger(last,v,level,TRIGGER_RISING)){ std::cout<<"Triggered at "<<i<<" value="<<v<<"\n"; fired=true;} last=v; }
  if (!fired) std::cout<<"No trigger fired\n";
  return 0;
}
