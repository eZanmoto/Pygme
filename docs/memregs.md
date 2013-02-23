Memory Registers
================

Sean Kelleher
-------------

### Definition

The memory registers are virtual registers for the GPU that are dedicated
sections of RAM, located in the IO segment of Zero-page RAM (0xFF00 - 0xFF80).

### Access Method

There are two main ways to implement the access of these registers. The first is
to manage dedicated variables which which will store the values of these
registers. This is achieved by hooking into the memory write method, and, when
the sections of memory representing the registers are being written to, write to
the variables instead.

A more modular approach is to have methods for reading the registers, returning
the values with the proper representation. This has the following benefits over
the variable management scheme:

+ The write method for memory can remain closed.
+ The write method for memory will not experience the bloat of additional
  behavioural hooks.
+ No extra components (variables) have to be managed and watched.
+ The management of each register is performed in dedicated methods, instead of
  all management being performed in the memory write method. This should prevent
  changes to the processing of one register having knock-on effects.
+ Making changes to the handling of the write method may have unexpected
  repercussions on the whole of the write method if data is manipulated inside
  the method. Having the tasks delegated to dedicated read methods will localize
  potential errors to the read methods themselves.
+ Adding side effects/modifications (possibly for debugging purposes, such as
  incrementing an access count or having a debugging hook) is impossible with
  raw variables.
