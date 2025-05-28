graph [
  directed 1
  multigraph 1
  node [
    id 0
    label "Landroid/content/BroadcastReceiver;-><init>()V>"
    external 1
    entrypoint 0
    native 0
    public 0
    static 0
    vm 0
    codesize 0
  ]
  node [
    id 1
    label "Lch/blinkenlights/battery/BlinkenlightsBatteryBootReceiver;-><init>()V"
    external 0
    entrypoint 1
    native 0
    public 1
    static 0
    vm "8733770405129"
    codesize 2
  ]
  node [
    id 2
    label "Landroid/content/Context;->startService(Landroid/content/Intent;)Landroid/content/ComponentName;>"
    external 1
    entrypoint 0
    native 0
    public 0
    static 0
    vm 0
    codesize 0
  ]
  node [
    id 3
    label "Lch/blinkenlights/battery/BlinkenlightsBatteryBootReceiver;->onReceive(Landroid/content/Context;"
    external 0
    entrypoint 1
    native 0
    public 1
    static 0
    vm "8733770405129"
    codesize 5
  ]
  node [
    id 4
    label "Landroid/content/Intent;-><init>(Landroid/content/Context;"
    external 1
    entrypoint 0
    native 0
    public 0
    static 0
    vm 0
    codesize 0
  ]
  edge [
    source 1
    target 0
    key 0
    offset 0
  ]
  edge [
    source 3
    target 4
    key 8
    offset 8
  ]
  edge [
    source 3
    target 2
    key 14
    offset 14
  ]
]
