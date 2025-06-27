package tn.esprit.spring;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class SimpleMathTest {

    @Test
    void testAddition() {
        int result = 2 + 3;
        assertEquals(5, result, "2 + 3 doit être égal à 5");
    }
}
