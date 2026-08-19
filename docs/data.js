// bench3 benchmark data (generated from results CSVs)
const BENCH = {
 "arms": [
  {
   "id": "deepseek-flash",
   "name": "DeepSeek V4 Flash",
   "vendor": "DeepSeek",
   "cloud": true,
   "color": "#7b61ff"
  },
  {
   "id": "deepseek-pro",
   "name": "DeepSeek V4 Pro",
   "vendor": "DeepSeek",
   "cloud": true,
   "color": "#4f7cff"
  },
  {
   "id": "gpt-sol",
   "name": "GPT-5.6 Sol",
   "vendor": "OpenAI",
   "cloud": true,
   "color": "#10a37f"
  },
  {
   "id": "grok",
   "name": "Grok 4.6",
   "vendor": "xAI",
   "cloud": true,
   "color": "#ff6b6b"
  },
  {
   "id": "mtplx",
   "name": "MTPLX \u00b7 Qwen 3.8 27B",
   "vendor": "Local (MTPLX)",
   "cloud": false,
   "color": "#4ade80"
  },
  {
   "id": "lunaroute",
   "name": "GLM 5.2 Vision",
   "vendor": "LunaRoute",
   "cloud": true,
   "color": "#f59e0b"
  }
 ],
 "categories": {
  "coding": {
   "deepseek-flash": {
    "n": 6,
    "passed": 6,
    "pct": 100.0
   },
   "deepseek-pro": {
    "n": 6,
    "passed": 6,
    "pct": 100.0
   },
   "gpt-sol": {
    "n": 6,
    "passed": 6,
    "pct": 100.0
   },
   "grok": {
    "n": 6,
    "passed": 6,
    "pct": 100.0
   },
   "mtplx": {
    "n": 3,
    "passed": 2,
    "pct": 66.7
   },
   "lunaroute": {
    "n": 3,
    "passed": 2,
    "pct": 66.7
   }
  },
  "agentic-workflow": {
   "deepseek-flash": {
    "n": 5,
    "passed": 5,
    "pct": 100.0
   },
   "deepseek-pro": {
    "n": 5,
    "passed": 5,
    "pct": 100.0
   },
   "gpt-sol": {
    "n": 5,
    "passed": 3,
    "pct": 60.0
   },
   "grok": {
    "n": 5,
    "passed": 5,
    "pct": 100.0
   },
   "mtplx": {
    "n": 2,
    "passed": 2,
    "pct": 100.0
   },
   "lunaroute": {
    "n": 2,
    "passed": 2,
    "pct": 100.0
   }
  },
  "reasoning": {
   "deepseek-flash": {
    "n": 14,
    "passed": 8,
    "pct": 57.1
   },
   "deepseek-pro": {
    "n": 14,
    "passed": 9,
    "pct": 64.3
   },
   "gpt-sol": {
    "n": 14,
    "passed": 14,
    "pct": 100.0
   },
   "grok": {
    "n": 14,
    "passed": 14,
    "pct": 100.0
   },
   "mtplx": {
    "n": 4,
    "passed": 4,
    "pct": 100.0
   },
   "lunaroute": {
    "n": 4,
    "passed": 4,
    "pct": 100.0
   }
  },
  "tool-use": {
   "deepseek-flash": {
    "n": 13,
    "passed": 7,
    "pct": 53.8
   },
   "deepseek-pro": {
    "n": 13,
    "passed": 8,
    "pct": 61.5
   },
   "gpt-sol": {
    "n": 13,
    "passed": 0,
    "pct": 0.0
   },
   "grok": {
    "n": 13,
    "passed": 2,
    "pct": 15.4
   },
   "mtplx": {
    "n": 3,
    "passed": 0,
    "pct": 0.0
   },
   "lunaroute": {
    "n": 3,
    "passed": 1,
    "pct": 33.3
   }
  },
  "creativity": {
   "deepseek-flash": {
    "n": 6,
    "passed": 6,
    "pct": 100.0
   },
   "deepseek-pro": {
    "n": 6,
    "passed": 6,
    "pct": 100.0
   },
   "gpt-sol": {
    "n": 6,
    "passed": 6,
    "pct": 100.0
   },
   "grok": {
    "n": 6,
    "passed": 6,
    "pct": 100.0
   },
   "mtplx": {
    "n": 2,
    "passed": 2,
    "pct": 100.0
   },
   "lunaroute": {
    "n": 2,
    "passed": 2,
    "pct": 100.0
   }
  },
  "writing": {
   "deepseek-flash": {
    "n": 6,
    "passed": 6,
    "pct": 100.0
   },
   "deepseek-pro": {
    "n": 6,
    "passed": 6,
    "pct": 100.0
   },
   "gpt-sol": {
    "n": 6,
    "passed": 6,
    "pct": 100.0
   },
   "grok": {
    "n": 6,
    "passed": 6,
    "pct": 100.0
   },
   "mtplx": {
    "n": 2,
    "passed": 2,
    "pct": 100.0
   },
   "lunaroute": {
    "n": 2,
    "passed": 2,
    "pct": 100.0
   }
  }
 },
 "tasks": [
  {
   "task": "a1_chained",
   "category": "?",
   "arms": {
    "deepseek-flash": {
     "passed": 2,
     "n": 2,
     "secs": [
      83,
      81
     ]
    },
    "deepseek-pro": {
     "passed": 2,
     "n": 2,
     "secs": [
      134,
      45
     ]
    },
    "gpt-sol": {
     "passed": 2,
     "n": 2,
     "secs": [
      96,
      105
     ]
    },
    "grok": {
     "passed": 2,
     "n": 2,
     "secs": [
      43,
      99
     ]
    },
    "mtplx": {
     "passed": 1,
     "n": 1,
     "secs": [
      1283
     ]
    },
    "lunaroute": {
     "passed": 1,
     "n": 1,
     "secs": [
      57
     ]
    }
   }
  },
  {
   "task": "a2_buildtestfix",
   "category": "?",
   "arms": {
    "deepseek-flash": {
     "passed": 3,
     "n": 3,
     "secs": [
      51,
      70,
      72
     ]
    },
    "deepseek-pro": {
     "passed": 3,
     "n": 3,
     "secs": [
      112,
      45,
      61
     ]
    },
    "gpt-sol": {
     "passed": 1,
     "n": 3,
     "secs": [
      80,
      70,
      64
     ]
    },
    "grok": {
     "passed": 3,
     "n": 3,
     "secs": [
      29,
      28,
      34
     ]
    },
    "mtplx": {
     "passed": 1,
     "n": 1,
     "secs": [
      278
     ]
    },
    "lunaroute": {
     "passed": 1,
     "n": 1,
     "secs": [
      298
     ]
    }
   }
  },
  {
   "task": "c1_deadlock",
   "category": "?",
   "arms": {
    "deepseek-flash": {
     "passed": 2,
     "n": 2,
     "secs": [
      151,
      236
     ]
    },
    "deepseek-pro": {
     "passed": 2,
     "n": 2,
     "secs": [
      189,
      207
     ]
    },
    "gpt-sol": {
     "passed": 2,
     "n": 2,
     "secs": [
      170,
      145
     ]
    },
    "grok": {
     "passed": 2,
     "n": 2,
     "secs": [
      209,
      242
     ]
    },
    "mtplx": {
     "passed": 1,
     "n": 1,
     "secs": [
      1391
     ]
    },
    "lunaroute": {
     "passed": 0,
     "n": 1,
     "secs": [
      598
     ]
    }
   }
  },
  {
   "task": "c2_perf",
   "category": "?",
   "arms": {
    "deepseek-flash": {
     "passed": 2,
     "n": 2,
     "secs": [
      176,
      184
     ]
    },
    "deepseek-pro": {
     "passed": 2,
     "n": 2,
     "secs": [
      110,
      459
     ]
    },
    "gpt-sol": {
     "passed": 2,
     "n": 2,
     "secs": [
      114,
      264
     ]
    },
    "grok": {
     "passed": 2,
     "n": 2,
     "secs": [
      80,
      185
     ]
    },
    "mtplx": {
     "passed": 0,
     "n": 1,
     "secs": [
      1800
     ]
    },
    "lunaroute": {
     "passed": 1,
     "n": 1,
     "secs": [
      328
     ]
    }
   }
  },
  {
   "task": "c3_adversarial",
   "category": "?",
   "arms": {
    "deepseek-flash": {
     "passed": 2,
     "n": 2,
     "secs": [
      23,
      19
     ]
    },
    "deepseek-pro": {
     "passed": 2,
     "n": 2,
     "secs": [
      22,
      342
     ]
    },
    "gpt-sol": {
     "passed": 2,
     "n": 2,
     "secs": [
      57,
      83
     ]
    },
    "grok": {
     "passed": 2,
     "n": 2,
     "secs": [
      20,
      22
     ]
    },
    "mtplx": {
     "passed": 1,
     "n": 1,
     "secs": [
      120
     ]
    },
    "lunaroute": {
     "passed": 1,
     "n": 1,
     "secs": [
      18
     ]
    }
   }
  },
  {
   "task": "creativity/k1_product",
   "category": "creativity",
   "arms": {
    "deepseek-flash": {
     "passed": 3,
     "n": 3,
     "secs": [
      13,
      9,
      11
     ]
    },
    "deepseek-pro": {
     "passed": 3,
     "n": 3,
     "secs": [
      16,
      16,
      18
     ]
    },
    "gpt-sol": {
     "passed": 3,
     "n": 3,
     "secs": [
      24,
      35,
      34
     ]
    },
    "grok": {
     "passed": 3,
     "n": 3,
     "secs": [
      30,
      21,
      33
     ]
    },
    "mtplx": {
     "passed": 1,
     "n": 1,
     "secs": [
      113
     ]
    },
    "lunaroute": {
     "passed": 1,
     "n": 1,
     "secs": [
      286
     ]
    }
   }
  },
  {
   "task": "creativity/k2_story",
   "category": "creativity",
   "arms": {
    "deepseek-flash": {
     "passed": 3,
     "n": 3,
     "secs": [
      4,
      5,
      4
     ]
    },
    "deepseek-pro": {
     "passed": 3,
     "n": 3,
     "secs": [
      5,
      5,
      4
     ]
    },
    "gpt-sol": {
     "passed": 3,
     "n": 3,
     "secs": [
      24,
      22,
      25
     ]
    },
    "grok": {
     "passed": 3,
     "n": 3,
     "secs": [
      42,
      61,
      70
     ]
    },
    "mtplx": {
     "passed": 1,
     "n": 1,
     "secs": [
      295
     ]
    },
    "lunaroute": {
     "passed": 1,
     "n": 1,
     "secs": [
      372
     ]
    }
   }
  },
  {
   "task": "reasoning/r1_tiling",
   "category": "reasoning",
   "arms": {
    "deepseek-flash": {
     "passed": 0,
     "n": 5,
     "secs": [
      198,
      195,
      200,
      200,
      199
     ]
    },
    "deepseek-pro": {
     "passed": 2,
     "n": 5,
     "secs": [
      216,
      195,
      137,
      229,
      218
     ]
    },
    "gpt-sol": {
     "passed": 5,
     "n": 5,
     "secs": [
      37,
      40,
      42,
      37,
      71
     ]
    },
    "grok": {
     "passed": 5,
     "n": 5,
     "secs": [
      154,
      133,
      121,
      167,
      147
     ]
    },
    "mtplx": {
     "passed": 1,
     "n": 1,
     "secs": [
      545
     ]
    },
    "lunaroute": {
     "passed": 1,
     "n": 1,
     "secs": [
      392
     ]
    }
   }
  },
  {
   "task": "reasoning/r2_expectedflips",
   "category": "reasoning",
   "arms": {
    "deepseek-flash": {
     "passed": 3,
     "n": 3,
     "secs": [
      8,
      6,
      7
     ]
    },
    "deepseek-pro": {
     "passed": 3,
     "n": 3,
     "secs": [
      15,
      18,
      21
     ]
    },
    "gpt-sol": {
     "passed": 3,
     "n": 3,
     "secs": [
      4,
      4,
      4
     ]
    },
    "grok": {
     "passed": 3,
     "n": 3,
     "secs": [
      14,
      18,
      12
     ]
    },
    "mtplx": {
     "passed": 1,
     "n": 1,
     "secs": [
      39
     ]
    },
    "lunaroute": {
     "passed": 1,
     "n": 1,
     "secs": [
      25
     ]
    }
   }
  },
  {
   "task": "reasoning/r3_die_expected",
   "category": "reasoning",
   "arms": {
    "deepseek-flash": {
     "passed": 3,
     "n": 3,
     "secs": [
      7,
      5,
      10
     ]
    },
    "deepseek-pro": {
     "passed": 3,
     "n": 3,
     "secs": [
      19,
      15,
      17
     ]
    },
    "gpt-sol": {
     "passed": 3,
     "n": 3,
     "secs": [
      7,
      6,
      7
     ]
    },
    "grok": {
     "passed": 3,
     "n": 3,
     "secs": [
      16,
      18,
      12
     ]
    },
    "mtplx": {
     "passed": 1,
     "n": 1,
     "secs": [
      25
     ]
    },
    "lunaroute": {
     "passed": 1,
     "n": 1,
     "secs": [
      53
     ]
    }
   }
  },
  {
   "task": "reasoning/r4_catalan",
   "category": "reasoning",
   "arms": {
    "deepseek-flash": {
     "passed": 2,
     "n": 3,
     "secs": [
      54,
      68,
      79
     ]
    },
    "deepseek-pro": {
     "passed": 1,
     "n": 3,
     "secs": [
      105,
      97,
      62
     ]
    },
    "gpt-sol": {
     "passed": 3,
     "n": 3,
     "secs": [
      7,
      8,
      6
     ]
    },
    "grok": {
     "passed": 3,
     "n": 3,
     "secs": [
      38,
      35,
      24
     ]
    },
    "mtplx": {
     "passed": 1,
     "n": 1,
     "secs": [
      96
     ]
    },
    "lunaroute": {
     "passed": 1,
     "n": 1,
     "secs": [
      74
     ]
    }
   }
  },
  {
   "task": "tool-use/t1_orchestrate",
   "category": "tool-use",
   "arms": {
    "deepseek-flash": {
     "passed": 4,
     "n": 5,
     "secs": [
      7,
      5,
      6,
      3,
      4
     ]
    },
    "deepseek-pro": {
     "passed": 5,
     "n": 5,
     "secs": [
      10,
      6,
      11,
      12,
      23
     ]
    },
    "gpt-sol": {
     "passed": 0,
     "n": 5,
     "secs": [
      4,
      7,
      5,
      14,
      4
     ]
    },
    "grok": {
     "passed": 0,
     "n": 5,
     "secs": [
      17,
      15,
      20,
      19,
      16
     ]
    },
    "mtplx": {
     "passed": 0,
     "n": 1,
     "secs": [
      38
     ]
    },
    "lunaroute": {
     "passed": 1,
     "n": 1,
     "secs": [
      19
     ]
    }
   }
  },
  {
   "task": "tool-use/t2_toolselect",
   "category": "tool-use",
   "arms": {
    "deepseek-flash": {
     "passed": 0,
     "n": 5,
     "secs": [
      1,
      1,
      3,
      2,
      2
     ]
    },
    "deepseek-pro": {
     "passed": 0,
     "n": 5,
     "secs": [
      4,
      3,
      6,
      4,
      5
     ]
    },
    "gpt-sol": {
     "passed": 0,
     "n": 5,
     "secs": [
      1,
      2,
      2,
      2,
      1
     ]
    },
    "grok": {
     "passed": 0,
     "n": 5,
     "secs": [
      4,
      4,
      5,
      6,
      6
     ]
    },
    "mtplx": {
     "passed": 0,
     "n": 1,
     "secs": [
      18
     ]
    },
    "lunaroute": {
     "passed": 0,
     "n": 1,
     "secs": [
      7
     ]
    }
   }
  },
  {
   "task": "tool-use/t3_inventory",
   "category": "tool-use",
   "arms": {
    "deepseek-flash": {
     "passed": 3,
     "n": 3,
     "secs": [
      5,
      6,
      6
     ]
    },
    "deepseek-pro": {
     "passed": 3,
     "n": 3,
     "secs": [
      13,
      14,
      45
     ]
    },
    "gpt-sol": {
     "passed": 0,
     "n": 3,
     "secs": [
      4,
      5,
      5
     ]
    },
    "grok": {
     "passed": 2,
     "n": 3,
     "secs": [
      25,
      11,
      24
     ]
    },
    "mtplx": {
     "passed": 0,
     "n": 1,
     "secs": [
      24
     ]
    },
    "lunaroute": {
     "passed": 0,
     "n": 1,
     "secs": [
      16
     ]
    }
   }
  },
  {
   "task": "writing/w1_explain",
   "category": "writing",
   "arms": {
    "deepseek-flash": {
     "passed": 3,
     "n": 3,
     "secs": [
      3,
      3,
      3
     ]
    },
    "deepseek-pro": {
     "passed": 3,
     "n": 3,
     "secs": [
      3,
      4,
      4
     ]
    },
    "gpt-sol": {
     "passed": 3,
     "n": 3,
     "secs": [
      5,
      4,
      9
     ]
    },
    "grok": {
     "passed": 3,
     "n": 3,
     "secs": [
      9,
      10,
      12
     ]
    },
    "mtplx": {
     "passed": 1,
     "n": 1,
     "secs": [
      28
     ]
    },
    "lunaroute": {
     "passed": 1,
     "n": 1,
     "secs": [
      57
     ]
    }
   }
  },
  {
   "task": "writing/w2_rewrite",
   "category": "writing",
   "arms": {
    "deepseek-flash": {
     "passed": 3,
     "n": 3,
     "secs": [
      1,
      1,
      1
     ]
    },
    "deepseek-pro": {
     "passed": 3,
     "n": 3,
     "secs": [
      2,
      1,
      2
     ]
    },
    "gpt-sol": {
     "passed": 3,
     "n": 3,
     "secs": [
      6,
      36,
      19
     ]
    },
    "grok": {
     "passed": 3,
     "n": 3,
     "secs": [
      95,
      92,
      86
     ]
    },
    "mtplx": {
     "passed": 1,
     "n": 1,
     "secs": [
      257
     ]
    },
    "lunaroute": {
     "passed": 1,
     "n": 1,
     "secs": [
      464
     ]
    }
   }
  }
 ],
 "tps": {
  "deepseek-flash": {
   "singleshot": {
    "mean": 112.1,
    "n": 39
   },
   "agentic": {
    "mean": 107.1,
    "n": 11
   },
   "all": 111.0
  },
  "deepseek-pro": {
   "singleshot": {
    "mean": 78.2,
    "n": 39
   },
   "agentic": {
    "mean": 83.5,
    "n": 11
   },
   "all": 79.4
  },
  "gpt-sol": {
   "singleshot": {
    "mean": 57.5,
    "n": 39
   },
   "agentic": {
    "mean": 41.1,
    "n": 11
   },
   "all": 53.9
  },
  "grok": {
   "singleshot": {
    "mean": 10.3,
    "n": 39
   },
   "agentic": {
    "mean": 31.1,
    "n": 11
   },
   "all": 14.8
  },
  "mtplx": {
   "singleshot": {
    "mean": 33.3,
    "n": 11
   },
   "agentic": {
    "mean": 19.7,
    "n": 5
   },
   "all": 29.0
  },
  "lunaroute": {
   "singleshot": {
    "mean": 35.1,
    "n": 11
   },
   "agentic": {
    "mean": 33.1,
    "n": 5
   },
   "all": 34.5
  }
 },
 "judged": {
  "deepseek-flash": {
   "mean": 4.36,
   "n": 12
  },
  "deepseek-pro": {
   "mean": 4.39,
   "n": 12
  },
  "gpt-sol": {
   "mean": 4.37,
   "n": 12
  },
  "grok": {
   "mean": 3.93,
   "n": 12
  },
  "mtplx": {
   "mean": 4.24,
   "n": 4
  },
  "lunaroute": {
   "mean": 4.38,
   "n": 3
  }
 },
 "overall": {
  "deepseek-flash": {
   "n": 50,
   "passed": 38,
   "pass_pct": 76.0,
   "cost_usd": 0.1034,
   "wall_s": 2491,
   "med_s": 7.0,
   "trials": [
    "1",
    "2",
    "3",
    "4",
    "5"
   ]
  },
  "deepseek-pro": {
   "n": 50,
   "passed": 40,
   "pass_pct": 80.0,
   "cost_usd": 0.3319,
   "wall_s": 3326,
   "med_s": 17.5,
   "trials": [
    "1",
    "2",
    "3",
    "4",
    "5"
   ]
  },
  "gpt-sol": {
   "n": 50,
   "passed": 35,
   "pass_pct": 70.0,
   "cost_usd": 3.6035,
   "wall_s": 1827,
   "med_s": 11.5,
   "trials": [
    "1",
    "2",
    "3",
    "4",
    "5"
   ]
  },
  "grok": {
   "n": 50,
   "passed": 39,
   "pass_pct": 78.0,
   "cost_usd": 0.8595,
   "wall_s": 2633,
   "med_s": 24.5,
   "trials": [
    "1",
    "2",
    "3",
    "4",
    "5"
   ]
  },
  "mtplx": {
   "n": 16,
   "passed": 12,
   "pass_pct": 75.0,
   "cost_usd": 0.0,
   "wall_s": 6350,
   "med_s": 116.5,
   "trials": [
    "1"
   ]
  },
  "lunaroute": {
   "n": 16,
   "passed": 13,
   "pass_pct": 81.2,
   "cost_usd": 0.0,
   "wall_s": 3064,
   "med_s": 65.5,
   "trials": [
    "1"
   ]
  }
 },
 "decode": {
  "mtp_vs_ar": {
   "mtp": "22\u201330",
   "ar": "13\u201318",
   "speedup": "1.6\u20131.7\u00d7",
   "burst": "2.6\u00d7"
  },
  "app_dashboard": 46.4,
  "cool_default": 36.2,
  "cool_greedy": 41.2,
  "hot_default": [
   25.7,
   25.9
  ],
  "hot_greedy": [
   28.5,
   34.0
  ]
 },
 "mlxfast": {
  "claim_speedup": 2.94,
  "claim_url": "https://www.yukon.org/mlxfast",
  "repo_url": "https://github.com/Layr-Labs/qwen-3.8-mtp-challenge",
  "our_machine": "MacBook Pro M5 Max \u00b7 64 GB \u00b7 hot + GPU in use by host",
  "legs": [
   {
    "depth": 0,
    "label": "True serial (MTP off)",
    "tps": 11.2,
    "speedup": 1.0,
    "accept": null
   },
   {
    "depth": 2,
    "label": "MTP depth 2",
    "tps": 19.1,
    "speedup": 1.7,
    "accept": 1.0
   },
   {
    "depth": 4,
    "label": "MTP depth 4",
    "tps": 21.1,
    "speedup": 1.88,
    "accept": 0.97
   },
   {
    "depth": 8,
    "label": "MTP depth 8 \u00b7 record submission",
    "tps": 23.3,
    "speedup": 2.07,
    "accept": 0.97
   }
  ],
  "parity": true,
  "stock_speedup": 2.53,
  "reference": {
   "serial_tps": 26.3,
   "mtp_tps": 77.7,
   "speedup": 2.95,
   "note": "thermally gated (\u226440\u00b0C) \u00b7 idle 128 GB M5 Max \u00b7 8 hidden prompts \u00d7 512 tok"
  },
  "mtplx_ref": "MTPLX on the same chip measured 1.6\u20132.6\u00d7 decode speedup"
 }
};
