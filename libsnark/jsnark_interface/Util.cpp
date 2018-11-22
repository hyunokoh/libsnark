#include "Util.hpp"

void readIds(char* str, std::vector<string>& vec){
	istringstream iss_i(str, istringstream::in);
	char id[80];
	while (iss_i >> id) {
		vec.push_back(id);
	}
}

FieldT readFieldElementFromHex(char* inputStr){
	char constStrDecimal[150];
	mpz_t integ;
	mpz_init_set_str(integ, inputStr, 16);
	mpz_get_str(constStrDecimal, 10, integ);
	mpz_clear(integ);
	FieldT f = FieldT(constStrDecimal);
	return f;

}
