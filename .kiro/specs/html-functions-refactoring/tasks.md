# Implementation Plan

- [x] 1. Create common.js module with all shared functions





  - Create new file `now_server/common.js`
  - Add JSDoc comments for all functions
  - Organize functions into logical sections (Performance, Color Extraction, Color Manipulation, etc.)
  - Export all functions to global scope for HTML files
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.1, 4.2, 4.3_

- [x] 1.1 Implement Performance Monitoring functions in common.js


  - Implement `logPerformance()` function
  - Initialize global `performanceStats` object
  - Initialize global `colorCache` Map
  - _Requirements: 1.4, 3.3_

- [x] 1.2 Implement Color Extraction functions in common.js


  - Implement `getColorAtPoint()` function
  - Implement `getEdgeColors()` function with caching
  - Implement `getDominantColors()` function with caching
  - Implement `getDominantColor()` function for backward compatibility
  - _Requirements: 1.2, 3.1, 3.3_

- [x] 1.3 Implement Color Manipulation functions in common.js


  - Implement `lightenColor()` function
  - Implement `darkenColor()` function
  - Implement `desaturateColor()` function
  - Implement `ensureLightColor()` function
  - _Requirements: 1.2, 3.1_

- [x] 1.4 Implement Color Utility functions in common.js


  - Implement `isColorDark()` function
  - Implement `isColorGray()` function
  - Implement `isRedOrPink()` function
  - Implement `getHue()` function
  - Implement `colorDistance()` function
  - Implement `hexToRgba()` function
  - Implement `parseColor()` function
  - _Requirements: 1.2, 3.1_

- [x] 1.5 Implement Progress Management functions in common.js


  - Implement `formatTime()` function
  - Implement `updateProgress()` function
  - Implement `startProgressUpdate()` function
  - Implement `stopProgressUpdate()` function
  - _Requirements: 1.3, 3.2_

- [x] 1.6 Implement Visualizer Management functions in common.js


  - Implement `createVisualizer()` function
  - Implement `animateVisualizer()` function
  - Implement `stopVisualizer()` function
  - _Requirements: 1.2, 3.2_

- [x] 1.7 Implement UI Update functions in common.js


  - Implement `transitionAmbientLight()` function
  - Implement `updateAmbientLight()` function
  - Implement `applyAutoColors()` function
  - _Requirements: 1.2, 3.1_

- [x] 2. Update visualisation.html to use common.js





  - Add script tag to load common.js before inline script
  - Remove duplicate function definitions
  - Update function calls to use functions from common.js
  - Test that all functionality works correctly
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 2.1 Refactor visualisation.html color extraction code


  - Remove `getColorAtPoint()`, `getEdgeColors()`, `getDominantColors()` definitions
  - Verify that functions from common.js are used correctly
  - _Requirements: 2.2, 3.1_


- [x] 2.2 Refactor visualisation.html progress management code

  - Remove `formatTime()`, `updateProgress()`, `startProgressUpdate()`, `stopProgressUpdate()` definitions
  - Update function calls to pass required parameters
  - _Requirements: 2.2, 3.2_


- [x] 2.3 Refactor visualisation.html visualizer code

  - Remove `createVisualizer()`, `animateVisualizer()`, `stopVisualizer()` definitions
  - Update function calls to pass required parameters
  - _Requirements: 2.2, 3.2_

- [x] 3. Update visualisation_horizontal.html to use common.js



  - Add script tag to load common.js before inline script
  - Remove all duplicate function definitions (getColorAtPoint, getEdgeColors, getDominantColors, formatTime, updateProgress, startProgressUpdate, stopProgressUpdate, createVisualizer, animateVisualizer, stopVisualizer)
  - Ensure colorCache and performanceStats use window.colorCache and window.performanceStats from common.js
  - Remove local logPerformance function definition
  - Test that all functionality works correctly
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Update visualisation_var2.html to use common.js





  - Add script tag to load common.js before inline script
  - Remove all duplicate function definitions (getColorAtPoint, getEdgeColors, getDominantColors, formatTime, updateProgress, startProgressUpdate, stopProgressUpdate, createVisualizer, animateVisualizer, stopVisualizer)
  - Ensure colorCache and performanceStats use window.colorCache and window.performanceStats from common.js
  - Remove local logPerformance function definition
  - Test that all functionality works correctly
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 5. Update visualisation_var3.html to use common.js






  - Add script tag to load common.js before inline script
  - Remove all duplicate function definitions (getColorAtPoint, getEdgeColors, getDominantColors, formatTime, updateProgress, startProgressUpdate, stopProgressUpdate, createVisualizer, animateVisualizer, stopVisualizer)
  - Ensure colorCache and performanceStats use window.colorCache and window.performanceStats from common.js
  - Remove local logPerformance function definition
  - Test that all functionality works correctly
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 6. Update visualisation_var3_horizontal.html to use common.js






  - Add script tag to load common.js before inline script
  - Remove all duplicate function definitions (getColorAtPoint, getEdgeColors, getDominantColors, formatTime, updateProgress, startProgressUpdate, stopProgressUpdate, createVisualizer, animateVisualizer, stopVisualizer)
  - Ensure colorCache and performanceStats use window.colorCache and window.performanceStats from common.js
  - Remove local logPerformance function definition
  - Test that all functionality works correctly
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 7. Final verification of all HTML files





  - Verify visualisation.html still works correctly (already refactored)
  - Verify visualisation_horizontal.html works correctly after refactoring
  - Verify visualisation_var2.html works correctly after refactoring
  - Verify visualisation_var3.html works correctly after refactoring
  - Verify visualisation_var3_horizontal.html works correctly after refactoring
  - Check that all files load common.js successfully
  - Verify no duplicate function definitions remain in any HTML file
  - Confirm browser console shows no errors
  - _Requirements: 2.4, 3.1, 3.2, 3.3, 3.4, 3.5_
