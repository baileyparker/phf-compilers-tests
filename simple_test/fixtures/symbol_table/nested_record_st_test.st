SCOPE BEGIN
  X =>
    RECORD BEGIN
      SCOPE BEGIN
        a =>
          VAR BEGIN
            type:
              ARRAY BEGIN
                type:
                  INTEGER
                length:
                  7
              END ARRAY
          END VAR
        b =>
          VAR BEGIN
            type:
              ARRAY BEGIN
                type:
                  INTEGER
                length:
                  7
              END ARRAY
          END VAR
        c =>
          VAR BEGIN
            type:
              RECORD BEGIN
                SCOPE BEGIN
                  a =>
                    VAR BEGIN
                      type:
                        INTEGER
                    END VAR
                  b =>
                    VAR BEGIN
                      type:
                        ARRAY BEGIN
                          type:
                            INTEGER
                          length:
                            14
                        END ARRAY
                    END VAR
                END SCOPE
              END RECORD
          END VAR
        d =>
          VAR BEGIN
            type:
              RECORD BEGIN
                SCOPE BEGIN
                  a =>
                    VAR BEGIN
                      type:
                        INTEGER
                    END VAR
                  b =>
                    VAR BEGIN
                      type:
                        ARRAY BEGIN
                          type:
                            INTEGER
                          length:
                            14
                        END ARRAY
                    END VAR
                END SCOPE
              END RECORD
          END VAR
      END SCOPE
    END RECORD
  a =>
    CONST BEGIN
      type:
        INTEGER
      value:
        47
    END CONST
  b =>
    INTEGER
  f =>
    ARRAY BEGIN
      type:
        INTEGER
      length:
        55
    END ARRAY
  i =>
    VAR BEGIN
      type:
        INTEGER
    END VAR
  q =>
    VAR BEGIN
      type:
        ARRAY BEGIN
          type:
            INTEGER
          length:
            12
        END ARRAY
    END VAR
  x =>
    VAR BEGIN
      type:
        INTEGER
    END VAR
END SCOPE
