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
      END SCOPE
    END RECORD
  a =>
    CONST BEGIN
      type:
        INTEGER
      value:
        47
    END CONST
  i =>
    VAR BEGIN
      type:
        INTEGER
    END VAR
END SCOPE
