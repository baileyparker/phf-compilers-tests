SCOPE BEGIN
  A =>
    ARRAY BEGIN
      type:
        RECORD BEGIN
          SCOPE BEGIN
            x =>
              VAR BEGIN
                type:
                  RECORD BEGIN
                    SCOPE BEGIN
                      a =>
                        VAR BEGIN
                          type:
                            RECORD BEGIN
                              SCOPE BEGIN
                                a =>
                                  VAR BEGIN
                                    type:
                                      INTEGER
                                  END VAR
                                x =>
                                  VAR BEGIN
                                    type:
                                      INTEGER
                                  END VAR
                              END SCOPE
                            END RECORD
                        END VAR
                      b =>
                        VAR BEGIN
                          type:
                            RECORD BEGIN
                              SCOPE BEGIN
                                a =>
                                  VAR BEGIN
                                    type:
                                      INTEGER
                                  END VAR
                                x =>
                                  VAR BEGIN
                                    type:
                                      INTEGER
                                  END VAR
                              END SCOPE
                            END RECORD
                        END VAR
                      q =>
                        VAR BEGIN
                          type:
                            ARRAY BEGIN
                              type:
                                INTEGER
                              length:
                                5
                            END ARRAY
                        END VAR
                    END SCOPE
                  END RECORD
              END VAR
          END SCOPE
        END RECORD
      length:
        6
    END ARRAY
  R =>
    RECORD BEGIN
      SCOPE BEGIN
        a =>
          VAR BEGIN
            type:
              RECORD BEGIN
                SCOPE BEGIN
                  a =>
                    VAR BEGIN
                      type:
                        INTEGER
                    END VAR
                  x =>
                    VAR BEGIN
                      type:
                        INTEGER
                    END VAR
                END SCOPE
              END RECORD
          END VAR
        b =>
          VAR BEGIN
            type:
              RECORD BEGIN
                SCOPE BEGIN
                  a =>
                    VAR BEGIN
                      type:
                        INTEGER
                    END VAR
                  x =>
                    VAR BEGIN
                      type:
                        INTEGER
                    END VAR
                END SCOPE
              END RECORD
          END VAR
        q =>
          VAR BEGIN
            type:
              ARRAY BEGIN
                type:
                  INTEGER
                length:
                  5
              END ARRAY
          END VAR
      END SCOPE
    END RECORD
  s =>
    CONST BEGIN
      type:
        INTEGER
      value:
        47
    END CONST
END SCOPE
